local msrpc = require "msrpc"
local nmap = require "nmap"
local smb = require "smb"
local stdnse = require "stdnse"
local string = require "string"
local table = require "table"

description = [[
Checks for vulnerabilities:
* MS08-067, a Windows RPC vulnerability
* Conficker, an infection by the Conficker worm
* Unnamed regsvc DoS, a denial-of-service vulnerability I accidentally found in Windows 2000
* SMBv2 exploit (CVE-2009-3103, Microsoft Security Advisory 975497)
* MS06-025, a Windows Ras RPC service vulnerability
* MS07-029, a Windows Dns Server RPC service vulnerability

WARNING: These checks are dangerous, and are very likely to bring down a server.
These should not be run in a production environment unless you (and, more importantly,
the business) understand the risks!

As a system administrator, performing these kinds of checks is crucial, because
a lot more damage can be done by a worm or a hacker using this vulnerability than
by a scanner. Penetration testers, on the other hand, might not want to use this
script -- crashing services is not generally a good way of sneaking through a
network.

If you set the script parameter <code>unsafe</code>, then scripts will run that are almost
(or totally) guaranteed to crash a vulnerable system; do NOT specify <code>unsafe</code>
in a production environment! And that isn't to say that non-unsafe scripts will
not crash a system, they're just less likely to.

If you set the script parameter <code>safe</code>, then script will run that rarely or never
crash a vulnerable system. No promises, though.

MS08-067. Checks if a host is vulnerable to MS08-067, a Windows RPC vulnerability that
can allow remote code execution.  Checking for MS08-067 is very dangerous, as the check
is likely to crash systems. On a fairly wide scan conducted by Brandon Enright, we determined
that on average, a vulnerable system is more likely to crash than to survive
the check. Out of 82 vulnerable systems, 52 crashed.
At the same time, MS08-067 is extremely critical to fix. Metasploit has a working and
stable exploit for it, and any system vulnerable can very easily be compromised.
Conficker. Checks if a host is infected with a known Conficker strain. This check
is based on the simple conficker scanner found on this page:
http://iv.cs.uni-bonn.de/wg/cs/applications/containing-conficker.
Thanks to the folks who wrote that scanner!

regsvc DoS. Checks if a host is vulnerable to a crash in regsvc, caused
by a null pointer dereference. I inadvertently discovered this crash while working
on <code>smb-enum-sessions</code>, and discovered that it was repeatable. It's been
reported to Microsoft (case #MSRC8742).

This check WILL crash the service, if it's vulnerable, and requires a guest account
or higher to work. It is considered <code>unsafe</code>.

SMBv2 DoS. Performs a denial-of-service against the vulnerability disclosed in
CVE-2009-3103. Checks if the server went offline. This works against Windows Vista
and some versions of Windows 7, and causes a bluescreen if successful. The
proof-of-concept code at http://seclists.org/fulldisclosure/2009/Sep/39 was used,
with one small change.

MS06-025. Vulnerability targets the <code>RasRpcSumbitRequest()</code> RPC method which is
a part of RASRPC interface that serves as a RPC service for configuring and
getting information from the Remote Access and Routing service. RASRPC can be
accessed using either "\ROUTER" SMB pipe or the "\SRVSVC" SMB pipe (usually on Windows XP machines).
This is in RPC world known as "ncan_np" RPC transport. <code>RasRpcSumbitRequest()</code>
method is a generic method which provides different functionalities according
to the <code>RequestBuffer</code> structure and particularly the <code>RegType</code> field within that
structure. <code>RegType</code> field is of <code>enum ReqTypes</code> type. This enum type lists all
the different available operation that can be performed using the <code>RasRpcSubmitRequest()</code>
RPC method. The one particular operation that this vuln targets is the <code>REQTYPE_GETDEVCONFIG</code>
request to get device information on the RRAS.

MS07-029. Vulnerability targets the <code>R_DnssrvQuery()</code> and <code>R_DnssrvQuery2()</code> RPC method which is
a part of DNS Server RPC interface that serves as a RPC service for configuring and
getting information from the DNS Server service. DNS Server RPC service can be
accessed using "\dnsserver" SMB named pipe. The vulnerability is triggered when
a long string is send as the "zone" parameter which causes the buffer overflow which
crashes the service.

(Note: if you have other SMB/MSRPC vulnerability checks you'd like to see added, and
you can show me a tool with a license that is compatible with Nmap's, post a request
on the nmap-dev mailing list and I'll add it to my list [Ron Bowes].)
]]
---
--@usage
-- nmap --script smb-check-vulns.nse -p445 <host>
-- sudo nmap -sU -sS --script smb-check-vulns.nse -p U:137,T:139 <host>
--
--@output
-- Host script results:
-- | smb-check-vulns:
-- |   MS08-067: NOT VULNERABLE
-- |   Conficker: Likely CLEAN
-- |   regsvc DoS: regsvc DoS: NOT VULNERABLE
-- |   SMBv2 DoS (CVE-2009-3103): NOT VULNERABLE
-- |   MS06-025: NO SERVICE (the Ras RPC service is inactive)
-- |_  MS07-029: NO SERVICE (the Dns Server RPC service is inactive)
--
-- @args unsafe If set, this script will run checks that, if the system isn't
--       patched, are basically guaranteed to crash something. Remember that
--       non-unsafe checks aren't necessarily safe either)
-- @args safe   If set, this script will only run checks that are known (or at
--       least suspected) to be safe.
-----------------------------------------------------------------------

author = "Ron Bowes"
copyright = "Ron Bowes"
license = "Same as Nmap--See http://nmap.org/book/man-legal.html"
categories = {"intrusive","exploit","dos","vuln"}
-- run after all smb-* scripts (so if it DOES crash something, it doesn't kill
-- other scans have had a chance to run)
dependencies = {
  "smb-brute", "smb-enum-sessions", "smb-security-mode",
  "smb-enum-shares", "smb-server-stats",
  "smb-enum-domains", "smb-enum-users", "smb-system-info",
  "smb-enum-groups", "smb-os-discovery", "smb-enum-processes",
  "smb-psexec",
};


hostrule = function(host)
  return smb.get_port(host) ~= nil
end

local VULNERABLE = 1
local PATCHED    = 2
local UNKNOWN    = 3
local NOTRUN     = 4
local INFECTED   = 5
local INFECTED2  = 6
local CLEAN      = 7
local NOTUP      = 8

---Check if the server is patched for MS08-067. This is done by calling NetPathCompare with an
-- illegal string. If the string is accepted, then the server is vulnerable; if it's rejected, then
-- you're safe (for now).
--
-- Based on a packet cap of this script, thanks go out to the author:
-- http://labs.portcullis.co.uk/application/ms08-067-check/
--
-- If there's a licensing issue, please let me (Ron Bowes) know so I can
--
-- NOTE: This CAN crash stuff (ie, crash svchost and force a reboot), so beware! In about 20
-- tests I did, it crashed once. This is not a guarantee.
--
--@param host The host object.
--@return (status, result) If status is false, result is an error code; otherwise, result is either
--        <code>VULNERABLE</code> for vulnerable, <code>PATCHED</code> for not vulnerable,
--        <code>UNKNOWN</code> if there was an error (likely vulnerable), <code>NOTRUN</code>
--        if this check was disabled, and <code>INFECTED</code> if it was patched by Conficker.
function check_ms08_067(host)
--  if(nmap.registry.args.safe ~= nil) then
--    return true, NOTRUN
--  end
--  if(nmap.registry.args.unsafe == nil) then
--    return true, NOTRUN
--  end
  local status, smbstate
  local bind_result, netpathcompare_result

  -- Create the SMB session
  status, smbstate = msrpc.start_smb(host, "\\\\BROWSER")
  if(status == false) then
    return false, smbstate
  end

  -- Bind to SRVSVC service
  status, bind_result = msrpc.bind(smbstate, msrpc.SRVSVC_UUID, msrpc.SRVSVC_VERSION, nil)
  if(status == false) then
    msrpc.stop_smb(smbstate)
    return false, bind_result
  end

  -- Call netpathcanonicalize
  -- status, netpathcanonicalize_result = msrpc.srvsvc_netpathcanonicalize(smbstate, host.ip, "\\a", "\\test\\")

  local path1 = "\\AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\\..\\n"
  local path2 = "\\n"
  status, netpathcompare_result = msrpc.srvsvc_netpathcompare(smbstate, host.ip, path1, path2, 1, 0)

  -- Stop the SMB session
  msrpc.stop_smb(smbstate)

  if(status == false) then
    if(string.find(netpathcompare_result, "WERR_INVALID_PARAMETER") ~= nil) then
      return true, INFECTED
    elseif(string.find(netpathcompare_result, "INVALID_NAME") ~= nil) then
      return true, PATCHED
    else
      return true, UNKNOWN, netpathcompare_result
    end
  end


  return true, VULNERABLE
end

---Returns the appropriate text to display, if any.
--
--@param check The name of the check; for example, 'ms08-067'.
--@param message The message to display, such as 'VULNERABLE' or 'PATCHED'.
--@param description [optional] Extra details about the message. nil for a blank message.
--@param minimum_verbosity The minimum verbosity level required before the message is displayed.
--@param minimum_debug [optional] The minimum debug level required before the message is displayed (default: 0).
--@return A string with a textual representation of the error (or empty string, if it was determined that the message shouldn't be displayed).
local function get_response(check, message, description, minimum_verbosity, minimum_debug)
  if(minimum_debug == nil) then
    minimum_debug = 0
  end

  -- Check if we have appropriate verbosity/debug
  if(nmap.verbosity() >= minimum_verbosity and nmap.debugging() >= minimum_debug) then
    if(description == nil or description == '') then
      return string.format("%s: %s", check, message)
    else
      return string.format("%s: %s (%s)", check, message, description)
    end
  else
    return nil
  end
end

action = function(host)

  local status, result, message
  local response = {}

  -- Check for ms08-067
  status, result, message = check_ms08_067(host)
  if(status == false) then
    table.insert(response, get_response("MS08-067", "ERROR", result, 0, 1))
  else
    if(result == VULNERABLE) then
      table.insert(response, get_response("MS08-067", "VULNERABLE",        nil,                               0))
    elseif(result == UNKNOWN) then
      table.insert(response, get_response("MS08-067", "LIKELY VULNERABLE", "host stopped responding",         1)) -- TODO: this isn't very accurate
    elseif(result == NOTRUN) then
      table.insert(response, get_response("MS08-067", "CHECK DISABLED",    "add '--script-args=unsafe=1' to run", 1))
    elseif(result == INFECTED) then
      table.insert(response, get_response("MS08-067", "NOT VULNERABLE",    "likely by Conficker",             0))
    else
      table.insert(response, get_response("MS08-067", "NOT VULNERABLE", nil, 1))
    end
  end

  return stdnse.format_output(true, response)
end
