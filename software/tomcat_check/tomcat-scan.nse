description = [[
Attempts to authenticate against apache tomcat manager console with default and weak passwords.
If the console is not found (/manager/html), a request is made to check for jboss jmx-console instead.
]]

-----------------------------------------------------------------
-- @output
-- PORT     STATE SERVICE VERSION
-- 8080/tcp open  http    Apache Tomcat/Coyote JSP engine 1.1
-- | tomcat-brute: HTTP/1.1 401 Unauthorized
-- | 
-- | Basic realm=Tomcat Manager Application
-- |_[+] Found combination username:password !
--
-------------------------------OR--------------------------------
-- @output
-- PORT     STATE SERVICE VERSION
-- 8080/tcp open  http    Apache Tomcat/Coyote JSP engine 1.1
-- | tomcat-brute: /manager/html is HTTP 404
-- |_[+] jboss jmx console is HTTP 200 !
--
-----------------------------------------------------------------
--
-- Apache tomcat vulnscan script
-- ver 0.2 (26-12-2010) by spdr <spdr01@gmail.com>
-- Todo: Better identification of tomcat
-- Checkout: http://www.binaryvision.org.il/
-----------------------------------------------------------------

author = "spdr"

license = "Same as Nmap--See http://nmap.org/book/man-legal.html"

categories = {"default", "auth", "intrusive"}

local shortport = require "shortport"
local http = require "http"

portrule = shortport.http

action = function(host, port)
  local www_authenticate
  local challenges, basic_challenge
  local authcombinations= {
    { username = "admin", password = ""},
    { username = "admin", password = "admin"},
    { username = "admin", password = "tomcat"},
    { username = "admin", password = "manager"},
    { username = "admin", password = "secret"},
    { username = "admin", password = "1234"},
    { username = "admin", password = "12345"},
    { username = "admin", password = "123456"},
    { username = "admin", password = "12345678"},
    { username = "admin", password = "password"},
    { username = "admin", password = "changeit"},
    { username = "admin", password = "changeme"},
    { username = "tomcat", password = "tomcat"},
    { username = "tomcat", password = ""},
    { username = "tomcat", password = "admin"},
    { username = "tomcat", password = "manager"},
    { username = "tomcat", password = "secret"},
    { username = "tomcat", password = "1234"},
    { username = "tomcat", password = "12345"},
    { username = "tomcat", password = "123123"},
    { username = "tomcat", password = "123321"},
    { username = "tomcat", password = "123456"},
    { username = "tomcat", password = "12345678"},
    { username = "manager", password = "manager"},
    { username = "manager", password = "tomcat"},
    { username = "manager", password = "admin"},
    { username = "manager", password = "1234"},
    { username = "manager", password = "12345"},
    { username = "manager", password = "123456"},
    { username = "manager", password = "123123"},
    { username = "manager", password = "1234578"},
  }

  local result = {}
  local answer = http.get(host, port, "/manager/html")
  local jboss = http.get(host, port, "/jmx-console/HtmlAdaptor")

  --- check for HTTP 404
  if answer.status == 404 then
    result[#result + 1] = string.format("/manager/html is HTTP %d.", answer.status)
  if jboss.status == 200 then
    result[#result + 1] = string.format("[+] Jboss JMX console is HTTP %d !", jboss.status)
  end
    return table.concat(result, "\n")
  end

  --- check for 401 response code
  if answer.status ~= 401 then
    result[#result + 1] = string.format("No auth required. (HTTP %d)", answer.status)
    return table.concat(result, "\n")
  end

  result[#result + 1] = answer["status-line"]

  www_authenticate = answer.header["www-authenticate"]
  if not www_authenticate then
    result[#result + 1] = string.format("Server returned status %d but no WWW-Authenticate.", answer.status)
    return table.concat(result, "\n")
  end
  challenges = http.parse_www_authenticate(www_authenticate)
  if not challenges then
    result[#result + 1] = string.format("Server returned status %d but the WWW-Authenticate header could not be parsed.", answer.status)
    result[#result + 1] = string.format("WWW-Authenticate: %s", www_authenticate)
    return table.concat(result, "\n")
  end

  basic_challenge = nil
  for _, challenge in ipairs(challenges) do
    if challenge.scheme == "Basic" then
      basic_challenge = challenge
    end
    local line = challenge.scheme
    for name, value in pairs(challenge.params) do
      line = line .. string.format(" %s=%s", name, value)
       if value ~= "Tomcat Manager Application" then -- Its not tomcat, save the effort ...
        result[#result + 1] = string.format("%s is not tomcat.", value)
        return table.concat(result, "\n")
       end
    end
    result[#result + 1] = line
  end

  if basic_challenge then
    for _, auth in ipairs(authcombinations) do 
      answer = http.get(host, port, '/manager/html', {auth = auth})
      if answer.status == 403 then
        result[#result + 1] = string.format("[=] Tomcat will accept %s:%s, but management is disbaled.", auth.username, auth.password, answer.status)
        return table.concat(result, "\n")
      end
      if answer.status ~= 401 and answer.status ~= 403 then
        result[#result + 1] = string.format("[+] Found combination %s:%s !", auth.username, auth.password)
        return table.concat(result, "\n")
      end
    end
 if answer.status == 401 then
        result[#result + 1] = string.format("[-] The password was not found.")
 end
  end

  return table.concat(result, "\n")
end
