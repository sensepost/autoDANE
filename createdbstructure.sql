--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET search_path = public, pg_catalog;

--
-- Name: adddomain(integer, character varying); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION adddomain(_footprint_id integer, _domain_name character varying) RETURNS void
    LANGUAGE plpgsql
    AS $$
declare _new_domain_id bigint;
begin
  if (select count(*) from domains where footprint_id = _footprint_id and upper(domain_name) = upper(_domain_name)) = 0 then
    insert into domains (footprint_id, domain_name) values (_footprint_id, upper(_domain_name)) returning cast(id as bigint) into _new_domain_id;
      
    execute executeTriggers(_footprint_id, _new_domain_id, 10, upper(_domain_name));
  end if;
end;
$$;


ALTER FUNCTION public.adddomain(_footprint_id integer, _domain_name character varying) OWNER TO postgres;

--
-- Name: adddomaincreds(integer, integer, character varying, character varying, character varying, character varying, character varying); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION adddomaincreds(_footprint_id integer, _host_data_id integer, _domain character varying, _username character varying, _cleartext_password character varying, _lm_hash character varying, _ntlm_hash character varying) RETURNS void
    LANGUAGE plpgsql
    AS $$
begin
  if (select count(*) from domain_credentials where footprint_id = _footprint_id and upper(domain) = upper(_domain) and upper(username) = upper(_username)) = 0 then
    insert into domain_credentials 
      (footprint_id, domain, username, cleartext_password, lm_hash, ntlm_hash) values
      (_footprint_id, _domain, _username, _cleartext_password, _lm_hash, _ntlm_hash);
  elseif (_cleartext_password != '') then
    update domain_credentials set cleartext_password = _cleartext_password where footprint_id = _footprint_id and upper(domain) = upper(_domain) and upper(username) = upper(_username);
  elseif (_ntlm_hash != '') then
    update domain_credentials set lm_hash = _lm_hash, ntlm_hash = _ntlm_hash where footprint_id = _footprint_id and upper(domain) = upper(_domain) and upper(username) = upper(_username);
  end if;
    
  execute addDomain(_footprint_id, _domain);
end;
$$;


ALTER FUNCTION public.adddomaincreds(_footprint_id integer, _host_data_id integer, _domain character varying, _username character varying, _cleartext_password character varying, _lm_hash character varying, _ntlm_hash character varying) OWNER TO postgres;

--
-- Name: adddomaingroup(integer, integer, character varying); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION adddomaingroup(_footprint_id integer, _domain_id integer, _group_name character varying) RETURNS void
    LANGUAGE plpgsql
    AS $$
begin
  if (select count(*) from domain_groups where footprint_id = _footprint_id and domain_id = _domain_id and group_name = _group_name) = 0 then
    insert into domain_groups (footprint_id, domain_id, group_name) values (_footprint_id, _domain_id, _group_name);
  end if;
end;
$$;


ALTER FUNCTION public.adddomaingroup(_footprint_id integer, _domain_id integer, _group_name character varying) OWNER TO postgres;

--
-- Name: adddomainusertogroup(integer, integer, character varying, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION adddomainusertogroup(_footprint_id integer, _domain_id integer, _username character varying, _domain_group_id integer) RETURNS void
    LANGUAGE plpgsql
    AS $$
declare _domain_credentials_id int;
declare _sub_group_id int;
declare _domain_name varchar;
begin
  if (select count(*) from domain_groups where footprint_id = _footprint_id and domain_id = _domain_id and group_name = _username) = 0 then
--     if (select count(*) from domain_credentials dc join domains d on d.domain_name = dc.domain where dc.footprint_id = d.footprint_id and d.id = _domain_id and d.footprint_id = _footprint_id and dc.username = _username) = 0 then
--      insert into domain_credentials 
--      (footprint_id, domain, username, cleartext_password) values
--      (_footprint_id, (select domain_name from domains where id = _domain_id), _username, '');
--    end if;
    select domain_name into _domain_name from domains where id = _domain_id;
    execute adddomaincreds(_footprint_id, 0, _domain_name, _username, '', '', '');
    
    select dc.id into _domain_credentials_id from domain_credentials dc join domains d on dc.domain = d.domain_name where upper(username) = upper(_username) and d.id = _domain_id;
    
    if (select count(*) from domain_user_group_map where domain_credentials_id = _domain_credentials_id and domain_group_id = _domain_group_id) = 0 then
      insert into domain_user_group_map (domain_credentials_id, domain_group_id) values (_domain_credentials_id, _domain_group_id);
    end if;
  else
    select id into _sub_group_id from domain_groups where footprint_id = _footprint_id and domain_id = _domain_id and group_name = _username;
    if (select count(*) from domain_sub_groups where parent_group_id = _domain_group_id and child_group_id = _sub_group_id) = 0 then
      insert into domain_sub_groups (parent_group_id, child_group_id) values (_domain_group_id, _sub_group_id);
    end if;
  end if;
end;
$$;


ALTER FUNCTION public.adddomainusertogroup(_footprint_id integer, _domain_id integer, _username character varying, _domain_group_id integer) OWNER TO postgres;

--
-- Name: addfulllistport(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION addfulllistport(_port_number integer) RETURNS void
    LANGUAGE plpgsql
    AS $$
begin
  if (select count(*) from ports_to_scan where type_id = 2 and port_number = _port_number) = 0 then
    insert into ports_to_scan (type_id, port_number) values (2, _port_number);
  end if;
end;
$$;


ALTER FUNCTION public.addfulllistport(_port_number integer) OWNER TO postgres;

--
-- Name: addhost(integer, character varying, character varying, boolean); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION addhost(_footprint_id integer, _ip_address character varying, _host_name character varying, _is_dc boolean) RETURNS void
    LANGUAGE plpgsql
    AS $$
DECLARE _net_range VARCHAR(45);
BEGIN
  _net_range := (select concat(SUBSTRING(_ip_address, 1, length(_ip_address) - position('.' in reverse(_ip_address))), '.0/24'));
    
  if (select count(*) from host_data where footprint_id = _footprint_id and ip_address = _ip_address) = 0 then
    insert into host_data (footprint_id, ip_address, host_name) values (_footprint_id, _ip_address, _host_name);
        
    execute executeTriggers(_footprint_id, currval('host_data_id_seq'), 1, _ip_address);
  end if;
    
  if (select count(*) from net_ranges where footprint_id = _footprint_id and net_range = _net_range) = 0 then
    insert into net_ranges (footprint_id, net_range) values (_footprint_id, _net_range);
    execute executeTriggers(_footprint_id, currval('net_ranges_id_seq'), 3, _net_range);
  end if;
    
  if _host_name != '' then 
    update host_data set host_name = _host_name where footprint_id = _footprint_id and ip_address = _ip_address;
  end if;
    
  if (_is_dc = True) then
    update host_data set is_dc = _is_dc where footprint_id = _footprint_id and ip_address = _ip_address;
  end if;
END;
$$;


ALTER FUNCTION public.addhost(_footprint_id integer, _ip_address character varying, _host_name character varying, _is_dc boolean) OWNER TO postgres;

--
-- Name: addlocalcredentials(integer, character varying, character varying, character varying, character varying); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION addlocalcredentials(_host_data_id integer, _username character varying, _cleartext_password character varying, _lm_hash character varying, _ntlm_hash character varying) RETURNS void
    LANGUAGE plpgsql
    AS $$
begin
	if (select count(*) from local_credentials where host_data_id = _host_data_id and username = _username) = 0 then
		insert into local_credentials (host_data_id, username) values (_host_data_id, _username);
    end if;
    
    if (_cleartext_password != '') then
		update local_credentials set cleartext_password = _cleartext_password where host_data_id = _host_data_id and username = _username;
	end if;
    
    if (_lm_hash != '' and _ntlm_hash != '') then
		update local_credentials set lm_hash = _lm_hash, ntlm_hash = _ntlm_hash where host_data_id = _host_data_id and username = _username;
    end if;
    
    if (select count(*) from local_credentials lc join local_credentials_map m on lc.id = m.local_credentials_id where lc.host_data_id = _host_data_id and lc.username = _username) = 0 then
		insert into local_credentials_map (local_credentials_id, host_data_id, valid) select id, host_data_id, true from local_credentials where host_data_id = _host_data_id and username = _username;
    end if;  
end;
$$;


ALTER FUNCTION public.addlocalcredentials(_host_data_id integer, _username character varying, _cleartext_password character varying, _lm_hash character varying, _ntlm_hash character varying) OWNER TO postgres;

--
-- Name: addport(integer, integer, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION addport(_footprint_id integer, _host_data_id integer, _port_num integer) RETURNS void
    LANGUAGE plpgsql
    AS $$
declare _new_port_id bigint;
begin
  if (select count(*) from port_data where host_data_id = _host_data_id and port_number = _port_num) = 0 then
    insert into port_data (host_data_id, port_number) values (_host_data_id, _port_num) returning cast(id as bigint) into _new_port_id;
    --select executeTriggers(_footprint_id, currval('port_data_id_seq'), 2, _port_num );
    execute executeTriggers(_footprint_id, _new_port_id, 2, _port_num::varchar );
  end if;
end;
$$;


ALTER FUNCTION public.addport(_footprint_id integer, _host_data_id integer, _port_num integer) OWNER TO postgres;

--
-- Name: addscopeitem(integer, integer, character varying); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION addscopeitem(_footprint_id integer, _item_type integer, _item_value character varying) RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
  if (select count(*) from scope where footprint_id = _footprint_id and item_type = _item_type and item_value = _item_value) = 0 then
    insert into scope (footprint_id, item_type, item_value) values (_footprint_id, _item_type, _item_value);
        
    if _item_type = 1 then
      execute executeTriggers(_footprint_id, currval('scope_id_seq'), 6, _item_value); 
    end if;
        
    if _item_type = 2 then
      execute executeTriggers(_footprint_id, currval('scope_id_seq'), 7, _item_value); 
    end if;
  end if;
END;
$$;


ALTER FUNCTION public.addscopeitem(_footprint_id integer, _item_type integer, _item_value character varying) OWNER TO postgres;

--
-- Name: addshortlistport(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION addshortlistport(_port_number integer) RETURNS void
    LANGUAGE plpgsql
    AS $$
begin
  if (select count(*) from ports_to_scan where type_id = 1 and port_number = _port_number) = 0 then
    insert into ports_to_scan (type_id, port_number) values (1, _port_number);
  end if;
end;
$$;


ALTER FUNCTION public.addshortlistport(_port_number integer) OWNER TO postgres;

--
-- Name: addtasklistitem(integer, integer, integer, boolean, boolean); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION addtasklistitem(_footprint_id integer, task_descriptions_id integer, _item_identifier integer, _in_progress boolean, _completed boolean) RETURNS integer
    LANGUAGE plpgsql
    AS $$
begin
insert into task_list 
(footprint_id, task_descriptions_id, item_identifier, in_progress, completed) values 
(_footprint_id, task_descriptions_id, _item_identifier, _in_progress, _completed); 

return(currval('task_list_id_seq'));
end;
$$;


ALTER FUNCTION public.addtasklistitem(_footprint_id integer, task_descriptions_id integer, _item_identifier integer, _in_progress boolean, _completed boolean) OWNER TO postgres;

--
-- Name: addtodomaincredentialsmap(integer, integer, integer, boolean); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION addtodomaincredentialsmap(_footprint_id integer, _host_data_id integer, _domain_credentials_id integer, _valid boolean) RETURNS void
    LANGUAGE plpgsql
    AS $$
begin
  if (select count(*) from domain_credentials_map where footprint_id = _footprint_id and host_data_id = _host_data_id and domain_credentials_id = _domain_credentials_id) = 0 then
    insert into domain_credentials_map
    (footprint_id, host_data_id, domain_credentials_id, valid) values
    (_footprint_id, _host_data_id, _domain_credentials_id, _valid);
  end if;

  if (_valid = true) then
    execute executeTriggers(_footprint_id, (select id from domain_credentials_map where footprint_id = _footprint_id and host_data_id = _host_data_id and domain_credentials_id = _domain_credentials_id), 9, '');
    update domain_credentials_map set valid = _valid where footprint_id = _footprint_id and host_data_id = _host_data_id and domain_credentials_id = _domain_credentials_id;
  end if;
end;
$$;


ALTER FUNCTION public.addtodomaincredentialsmap(_footprint_id integer, _host_data_id integer, _domain_credentials_id integer, _valid boolean) OWNER TO postgres;

--
-- Name: addtoken(integer, character varying); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION addtoken(_host_id integer, _token character varying) RETURNS void
    LANGUAGE plpgsql
    AS $$
begin
  if (select count(*) from tokens where host_id = _host_id and token = _token) = 0 then
    insert into tokens (host_id, token) values (_host_id, _token);
  end if;
end;
$$;


ALTER FUNCTION public.addtoken(_host_id integer, _token character varying) OWNER TO postgres;

--
-- Name: addtolocalcredentialsmap(integer, integer, boolean); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION addtolocalcredentialsmap(_host_data_id integer, _local_credentials_id integer, _valid boolean) RETURNS void
    LANGUAGE plpgsql
    AS $$
declare _username varchar(45);
declare _cleartext_password varchar(45);
declare _lm_hash varchar(45);
declare _ntlm_hash varchar(45);
declare credentials_id int;
begin
  if (_valid) = true then
    select username, cleartext_password, lm_hash, ntlm_hash into _username, _cleartext_password, _lm_hash, _ntlm_hash  from local_credentials where id = _local_credentials_id;
    select addLocalCredentials(_host_data_id, _username, _cleartext_password, _lm_hash, _ntlm_hash);
        
    select id into credentials_id from local_credentials where (host_data_id, username, cleartext_password) in (select hd.id, lc.username, lc.cleartext_password from host_data hd, local_credentials lc where hd.id = _host_data_id and lc.id = _local_credentials_id);
    select executeTriggers((select footprint_id from host_data where id = _host_data_id), credentials_id, 5, '');
  else
    if (select count(*) from local_credentials_map where host_data_id = _host_data_id and local_credentials_id = _local_credentials_id) = 0 then
      insert into local_credentials_map (host_data_id, local_credentials_id, valid) values (_host_data_id, _local_credentials_id, _valid);
    end if;
  end if;
end;
$$;


ALTER FUNCTION public.addtolocalcredentialsmap(_host_data_id integer, _local_credentials_id integer, _valid boolean) OWNER TO postgres;

--
-- Name: addvulnerability(integer, integer, integer, character varying); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION addvulnerability(_footprint_id integer, _port_data_id integer, _vulnerability_description_id integer, _details character varying) RETURNS void
    LANGUAGE plpgsql
    AS $$
declare _new_vuln_id bigint;
begin
  if (select count(*) from vulnerabilities where port_data_id = _port_data_id and vulnerability_descriptions_id = _vulnerability_description_id) = 0 then
    insert into vulnerabilities (port_data_id, vulnerability_descriptions_id, details) values (_port_data_id, _vulnerability_description_id, _details) returning cast(id as bigint) into _new_vuln_id;

    execute executeTriggers(_footprint_id, _new_vuln_id, 4, (select description from vulnerability_descriptions where id = _vulnerability_description_id));
  end if;
end;
$$;


ALTER FUNCTION public.addvulnerability(_footprint_id integer, _port_data_id integer, _vulnerability_description_id integer, _details character varying) OWNER TO postgres;

--
-- Name: addwebsite(integer, character varying, text, text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION addwebsite(_port_data_id integer, _html_title character varying, _html_body text, _screenshot text) RETURNS void
    LANGUAGE plpgsql
    AS $$
begin
  if (select count(*) from websites where port_data_id = _port_data_id) = 0 then
    insert into websites (port_data_id, html_title, html_body, screenshot) values (_port_data_id, _html_title, _html_body, _screenshot);
  end if;
end;
$$;


ALTER FUNCTION public.addwebsite(_port_data_id integer, _html_title character varying, _html_body text, _screenshot text) OWNER TO postgres;

--
-- Name: countdomaingroupstoexpand(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION countdomaingroupstoexpand(_footprint_id integer) RETURNS integer
    LANGUAGE plpgsql
    AS $$
begin
	return (
	select 
		count(*)
	from
	       domain_groups dg
	       join domains d on d.id = dg.domain_id and d.footprint_id = dg.footprint_id
	       join domain_credentials dc on d.domain_name = dc.domain
	       join domain_credentials_map m on m.domain_credentials_id = dc.id
	       join host_data hd on m.host_data_id = hd.id
	where
	       d.footprint_id = dc.footprint_id and
	       d.footprint_id = hd.footprint_id and
	       d.footprint_id = m.footprint_id and
	       m.valid = true and    
	       dg.users_gathered = false and 
	       m.psexec_failed = false and 
	       m.dgu_failed = false and
	       dg.id not in (select item_identifier from task_list where task_descriptions_id = 26 and footprint_id = _footprint_id and in_progress = true) and
	       hd.footprint_id = _footprint_id );
end;
$$;


ALTER FUNCTION public.countdomaingroupstoexpand(_footprint_id integer) OWNER TO postgres;

--
-- Name: createfootprint(character varying); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION createfootprint(_footprint_name character varying) RETURNS integer
    LANGUAGE plpgsql
    AS $$
  BEGIN
    if (select count(*) from footprints where footprint_name = _footprint_name) = 0 then
      insert into footprints (footprint_name) values (_footprint_name);
    end if;
	
    return (select id from footprints where footprint_name = _footprint_name);
  END;
$$;


ALTER FUNCTION public.createfootprint(_footprint_name character varying) OWNER TO postgres;

--
-- Name: deleteportfromlist(integer, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION deleteportfromlist(_type_id integer, _port_number integer) RETURNS void
    LANGUAGE plpgsql
    AS $$
begin
  delete from ports_to_scan where type_id = _type_id and port_number = _port_number;
end;
$$;


ALTER FUNCTION public.deleteportfromlist(_type_id integer, _port_number integer) OWNER TO postgres;

--
-- Name: executetriggers(integer, bigint, integer, character varying); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION executetriggers(_footprint_id integer, _item_identifier bigint, _trigger_event_id integer, _value character varying) RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
  insert into task_list (footprint_id, task_descriptions_id, item_identifier) 
  select 
    _footprint_id as footprint_id, td.id as task_descriptions_id, _item_identifier as item_identifier
  from 
    task_categories tc
    join task_descriptions td on tc.id = td.task_categories_id
    join trigger_events te on te.task_descriptions_id = td.id
    join trigger_descriptions trd on trd.id = te.trigger_descriptions_id
  where 
    trd.id = _trigger_event_id and
    _value like te.value_mask and 
    te.enabled = true;
END;
$$;


ALTER FUNCTION public.executetriggers(_footprint_id integer, _item_identifier bigint, _trigger_event_id integer, _value character varying) OWNER TO postgres;

--
-- Name: getdomaincredstoretry(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION getdomaincredstoretry(_footprint_id integer) RETURNS TABLE(host_data_id integer, ip_address character varying, domain_creds_id integer, domain character varying, username character varying, cleartext_password character varying)
    LANGUAGE plpgsql
    AS $$
declare _new_map_id bigint;
begin
        insert into domain_credentials_map (footprint_id, host_data_id, domain_credentials_id)
        (select
                hd.footprint_id, hd.id, dc.id
        from
                domain_credentials dc
                join host_data hd on hd.footprint_id = dc.footprint_id
                join port_data pd on pd.host_data_id = hd.id and pd.port_number = 445 and
                (hd.id, dc.id) not in (select m.host_data_id, m.domain_credentials_id from domain_credentials_map m)
        where
                dc.valid = true and
                hd.footprint_id = _footprint_id and
		hd.is_dc in (true)
        limit 1) returning id into _new_map_id;

        return query 
        select
                hd.id, hd.ip_address, dc.id, dc.domain, dc.username, dc.cleartext_password
        from
                domain_credentials_map m
                join host_data hd on hd.id = m.host_data_id
                join domain_credentials dc on dc.id = m.domain_credentials_id
        where
		hd.footprint_id = _footprint_id and 
                m.id = _new_map_id;
end;
$$;


ALTER FUNCTION public.getdomaincredstoretry(_footprint_id integer) OWNER TO postgres;

--
-- Name: getdomaincredstoverify(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION getdomaincredstoverify(_footprint_id integer) RETURNS TABLE(domain_credentials_id integer, ip_address character varying, domain character varying, username character varying, cleartext_password character varying, host_data_id integer, task_list_id integer)
    LANGUAGE plpgsql
    AS $$
declare _new_task_id bigint;
begin
        insert into task_list (footprint_id, task_descriptions_id, item_identifier, in_progress)
        (select
                _footprint_id, 19, dc.id, True
        from
                domain_credentials dc
                join domains d on upper(d.domain_name) = upper(dc.domain) and dc.footprint_id = d.footprint_id
                join host_data hd on upper(hd.domain) = upper(d.domain_name) and hd.footprint_id = dc.footprint_id
                join port_data pd on pd.host_data_id = hd.id
        where
                hd.footprint_id = _footprint_id and
                pd.port_number = 445 and
                dc.cleartext_password != '' and
                dc.verified = false and
                dc.id not in (select m.domain_credentials_id from domain_credentials_map m where m.footprint_id = _footprint_id) and
                dc.id not in (select tl.item_identifier from task_list tl where tl.footprint_id = _footprint_id and tl.task_descriptions_id = 19 and (tl.in_progress = true or tl.completed = true)) and
                hd.is_dc = true limit 1) returning task_list.id into _new_task_id;

        return query 
        select
                dc.id, hd.ip_address, dc.domain, dc.username, dc.cleartext_password, hd.id, tl.id
        from
                domain_credentials dc
                join domains d on upper(d.domain_name) = upper(dc.domain) and dc.footprint_id = d.footprint_id
                join host_data hd on upper(hd.domain) = upper(d.domain_name) and hd.footprint_id = dc.footprint_id
                join port_data pd on pd.host_data_id = hd.id
        join task_list tl on tl.item_identifier = dc.id
        where
                tl.id = _new_task_id and pd.port_number = 445 and task_descriptions_id = 19 and hd.is_dc = true and hd.footprint_id = _footprint_id;

end;
$$;


ALTER FUNCTION public.getdomaincredstoverify(_footprint_id integer) OWNER TO postgres;

--
-- Name: getdomaingrouptoexpand(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION getdomaingrouptoexpand(_footprint_id integer) RETURNS TABLE(domain_id integer, ip_address character varying, domain_name character varying, username character varying, cleartext_password character varying, map_id integer, group_name character varying, group_id integer)
    LANGUAGE plpgsql
    AS $$
begin
	return query
	select 
		d.id,
		hd.ip_address, 
		dc.domain, dc.username, dc.cleartext_password,
		m.id,
		dg.group_name, dg.id
	from
	       domain_groups dg
	       join domains d on d.id = dg.domain_id and d.footprint_id = dg.footprint_id
	       join domain_credentials dc on d.domain_name = dc.domain
	       join domain_credentials_map m on m.domain_credentials_id = dc.id
	       join host_data hd on m.host_data_id = hd.id
	where
	       d.footprint_id = dc.footprint_id and
	       d.footprint_id = hd.footprint_id and
	       d.footprint_id = m.footprint_id and
	       m.valid = true and    
	       dg.users_gathered = false and 
	       m.psexec_failed = false and 
	       m.dgu_failed = false and
	       dg.id not in (select item_identifier from task_list where task_descriptions_id = 26 and footprint_id = _footprint_id and in_progress = true) and
	       hd.footprint_id = _footprint_id
        order by dg.id
	limit 1;
end;
$$;


ALTER FUNCTION public.getdomaingrouptoexpand(_footprint_id integer) OWNER TO postgres;

--
-- Name: getpendingtask(integer, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION getpendingtask(_footprint_id integer, _task_descriptions_id integer) RETURNS TABLE(task_id integer, item_identifier integer)
    LANGUAGE plpgsql
    AS $$
declare _task_id int;
declare _item_identifier int;
begin

UPDATE task_list s
SET    in_progress = true
FROM  (
   SELECT    tl.id, tl.item_identifier
   FROM      task_list tl
   WHERE     tl.in_progress = false AND
             tl.completed = false AND
             tl.task_descriptions_id = _task_descriptions_id AND
             tl.footprint_id = _footprint_id AND
             pg_try_advisory_xact_lock(tl.id)
   ORDER BY  id
   LIMIT     1
   FOR       UPDATE
   ) sub
WHERE  s.id = sub.id
RETURNING s.id, s.item_identifier into _task_id, _item_identifier;
return QUERY select _task_id, _item_identifier;
--select _task_id, _item_identifier;
end;
$$;


ALTER FUNCTION public.getpendingtask(_footprint_id integer, _task_descriptions_id integer) OWNER TO postgres;

--
-- Name: setdomaincredsverified(integer, integer, boolean); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION setdomaincredsverified(_footprint_id integer, _domain_creds_id integer, _valid boolean) RETURNS void
    LANGUAGE plpgsql
    AS $$
begin
	update domain_credentials set verified = true, valid = _valid where id = _domain_creds_id;
end;
$$;


ALTER FUNCTION public.setdomaincredsverified(_footprint_id integer, _domain_creds_id integer, _valid boolean) OWNER TO postgres;

--
-- Name: test(character varying); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION test(_ip_address character varying) RETURNS TABLE(a character varying, b character varying)
    LANGUAGE plpgsql
    AS $$
  DECLARE _net_range VARCHAR(45);
begin
  _net_range := 'test';
  raise notice 'hello %', 'abc';
  return query select _ip_address,_ip_address;
end;
$$;


ALTER FUNCTION public.test(_ip_address character varying) OWNER TO postgres;

--
-- Name: updatetaskstatus(integer, boolean, boolean, text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION updatetaskstatus(_task_id integer, _in_progress boolean, _completed boolean, _log text) RETURNS void
    LANGUAGE plpgsql
    AS $$
begin
	update task_list set in_progress = _in_progress, completed = _completed, log = _log where id = _task_id;
end;
$$;


ALTER FUNCTION public.updatetaskstatus(_task_id integer, _in_progress boolean, _completed boolean, _log text) OWNER TO postgres;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: domain_credentials; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE domain_credentials (
    id integer NOT NULL,
    footprint_id integer NOT NULL,
    domain character varying(45) NOT NULL,
    username character varying(45) NOT NULL,
    cleartext_password character varying(45) DEFAULT ''::character varying NOT NULL,
    verified boolean DEFAULT false NOT NULL,
    lm_hash character varying(45) DEFAULT ''::character varying NOT NULL,
    ntlm_hash character varying(45) DEFAULT ''::character varying NOT NULL,
    valid boolean DEFAULT false NOT NULL
);


ALTER TABLE domain_credentials OWNER TO postgres;

--
-- Name: domain_credentials_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE domain_credentials_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE domain_credentials_id_seq OWNER TO postgres;

--
-- Name: domain_credentials_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE domain_credentials_id_seq OWNED BY domain_credentials.id;


--
-- Name: domain_credentials_map; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE domain_credentials_map (
    id integer NOT NULL,
    footprint_id integer NOT NULL,
    host_data_id integer NOT NULL,
    domain_credentials_id integer NOT NULL,
    valid boolean DEFAULT false NOT NULL,
    psexec_failed boolean DEFAULT false NOT NULL,
    dgu_failed boolean DEFAULT false NOT NULL
);


ALTER TABLE domain_credentials_map OWNER TO postgres;

--
-- Name: domain_credentials_map_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE domain_credentials_map_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE domain_credentials_map_id_seq OWNER TO postgres;

--
-- Name: domain_credentials_map_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE domain_credentials_map_id_seq OWNED BY domain_credentials_map.id;


--
-- Name: domain_groups; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE domain_groups (
    id integer NOT NULL,
    footprint_id integer NOT NULL,
    domain_id integer NOT NULL,
    group_name character varying(45) NOT NULL,
    users_gathered boolean DEFAULT false
);


ALTER TABLE domain_groups OWNER TO postgres;

--
-- Name: domain_groups_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE domain_groups_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE domain_groups_id_seq OWNER TO postgres;

--
-- Name: domain_groups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE domain_groups_id_seq OWNED BY domain_groups.id;


--
-- Name: domain_sub_groups; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE domain_sub_groups (
    id integer NOT NULL,
    parent_group_id integer,
    child_group_id integer
);


ALTER TABLE domain_sub_groups OWNER TO postgres;

--
-- Name: domain_sub_groups_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE domain_sub_groups_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE domain_sub_groups_id_seq OWNER TO postgres;

--
-- Name: domain_sub_groups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE domain_sub_groups_id_seq OWNED BY domain_sub_groups.id;


--
-- Name: domain_user_group_map; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE domain_user_group_map (
    id integer NOT NULL,
    domain_credentials_id integer,
    domain_group_id integer
);


ALTER TABLE domain_user_group_map OWNER TO postgres;

--
-- Name: domain_user_group_map_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE domain_user_group_map_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE domain_user_group_map_id_seq OWNER TO postgres;

--
-- Name: domain_user_group_map_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE domain_user_group_map_id_seq OWNED BY domain_user_group_map.id;


--
-- Name: domains; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE domains (
    id integer NOT NULL,
    footprint_id integer NOT NULL,
    domain_name character varying(45) NOT NULL,
    info_gathered boolean DEFAULT false NOT NULL,
    hashes_extracted boolean DEFAULT false NOT NULL
);


ALTER TABLE domains OWNER TO postgres;

--
-- Name: domains_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE domains_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE domains_id_seq OWNER TO postgres;

--
-- Name: domains_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE domains_id_seq OWNED BY domains.id;


--
-- Name: exploit_logs; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE exploit_logs (
    id integer NOT NULL,
    host_data_id integer NOT NULL,
    vulnerability_description_id integer NOT NULL,
    log text NOT NULL
);


ALTER TABLE exploit_logs OWNER TO postgres;

--
-- Name: exploit_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE exploit_logs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE exploit_logs_id_seq OWNER TO postgres;

--
-- Name: exploit_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE exploit_logs_id_seq OWNED BY exploit_logs.id;


--
-- Name: footprints; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE footprints (
    id integer NOT NULL,
    footprint_name character varying(45) NOT NULL
);


ALTER TABLE footprints OWNER TO postgres;

--
-- Name: footprints_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE footprints_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE footprints_id_seq OWNER TO postgres;

--
-- Name: footprints_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE footprints_id_seq OWNED BY footprints.id;


--
-- Name: host_data; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE host_data (
    id integer NOT NULL,
    footprint_id integer NOT NULL,
    ip_address character varying(45) NOT NULL,
    host_name character varying(45) DEFAULT ''::character varying NOT NULL,
    computer_name character varying(45) DEFAULT ''::character varying NOT NULL,
    os character varying(100) DEFAULT ''::character varying NOT NULL,
    architecture character varying(45) DEFAULT ''::character varying NOT NULL,
    system_language character varying(45) DEFAULT ''::character varying NOT NULL,
    domain character varying(45) DEFAULT ''::character varying NOT NULL,
    is_dc boolean DEFAULT false NOT NULL,
    successful_info_gather boolean DEFAULT false NOT NULL
);


ALTER TABLE host_data OWNER TO postgres;

--
-- Name: host_data_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE host_data_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE host_data_id_seq OWNER TO postgres;

--
-- Name: host_data_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE host_data_id_seq OWNED BY host_data.id;


--
-- Name: local_credentials; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE local_credentials (
    id integer NOT NULL,
    host_data_id integer NOT NULL,
    username character varying(45) NOT NULL,
    cleartext_password character varying(100) DEFAULT ''::character varying NOT NULL,
    lm_hash character varying(45) DEFAULT ''::character varying NOT NULL,
    ntlm_hash character varying(45) DEFAULT ''::character varying NOT NULL
);


ALTER TABLE local_credentials OWNER TO postgres;

--
-- Name: local_credentials_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE local_credentials_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE local_credentials_id_seq OWNER TO postgres;

--
-- Name: local_credentials_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE local_credentials_id_seq OWNED BY local_credentials.id;


--
-- Name: local_credentials_map; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE local_credentials_map (
    id integer NOT NULL,
    host_data_id integer,
    local_credentials_id integer,
    valid boolean DEFAULT false
);


ALTER TABLE local_credentials_map OWNER TO postgres;

--
-- Name: local_credentials_map_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE local_credentials_map_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE local_credentials_map_id_seq OWNER TO postgres;

--
-- Name: local_credentials_map_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE local_credentials_map_id_seq OWNED BY local_credentials_map.id;


--
-- Name: net_ranges; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE net_ranges (
    id integer NOT NULL,
    footprint_id integer NOT NULL,
    net_range character varying(45) NOT NULL
);


ALTER TABLE net_ranges OWNER TO postgres;

--
-- Name: net_ranges_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE net_ranges_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE net_ranges_id_seq OWNER TO postgres;

--
-- Name: net_ranges_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE net_ranges_id_seq OWNED BY net_ranges.id;


--
-- Name: port_data; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE port_data (
    id integer NOT NULL,
    host_data_id integer NOT NULL,
    port_number integer NOT NULL
);


ALTER TABLE port_data OWNER TO postgres;

--
-- Name: port_data_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE port_data_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE port_data_id_seq OWNER TO postgres;

--
-- Name: port_data_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE port_data_id_seq OWNED BY port_data.id;


--
-- Name: ports_to_scan; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE ports_to_scan (
    id integer NOT NULL,
    type_id integer,
    port_number integer
);


ALTER TABLE ports_to_scan OWNER TO postgres;

--
-- Name: ports_to_scan_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE ports_to_scan_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE ports_to_scan_id_seq OWNER TO postgres;

--
-- Name: ports_to_scan_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE ports_to_scan_id_seq OWNED BY ports_to_scan.id;


--
-- Name: scope; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE scope (
    id integer NOT NULL,
    footprint_id integer NOT NULL,
    item_type integer NOT NULL,
    item_value character varying(45) NOT NULL
);


ALTER TABLE scope OWNER TO postgres;

--
-- Name: scope_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE scope_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE scope_id_seq OWNER TO postgres;

--
-- Name: scope_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE scope_id_seq OWNED BY scope.id;


--
-- Name: task_categories; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE task_categories (
    id integer NOT NULL,
    category character varying(45) DEFAULT NULL::character varying,
    description character varying(450) DEFAULT NULL::character varying,
    position_id integer
);


ALTER TABLE task_categories OWNER TO postgres;

--
-- Name: task_categories_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE task_categories_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE task_categories_id_seq OWNER TO postgres;

--
-- Name: task_categories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE task_categories_id_seq OWNED BY task_categories.id;


--
-- Name: task_descriptions; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE task_descriptions (
    id integer NOT NULL,
    task_categories_id integer,
    task_name character varying(45) DEFAULT NULL::character varying,
    description text,
    file_name character varying(450) DEFAULT NULL::character varying,
    uses_metasploit boolean NOT NULL,
    is_recursive boolean DEFAULT false NOT NULL,
    enabled boolean DEFAULT false NOT NULL
);


ALTER TABLE task_descriptions OWNER TO postgres;

--
-- Name: task_descriptions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE task_descriptions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE task_descriptions_id_seq OWNER TO postgres;

--
-- Name: task_descriptions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE task_descriptions_id_seq OWNED BY task_descriptions.id;


--
-- Name: task_list; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE task_list (
    id integer NOT NULL,
    footprint_id integer NOT NULL,
    task_descriptions_id integer NOT NULL,
    item_identifier integer DEFAULT 0 NOT NULL,
    in_progress boolean DEFAULT false NOT NULL,
    completed boolean DEFAULT false NOT NULL,
    log text
);


ALTER TABLE task_list OWNER TO postgres;

--
-- Name: task_list_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE task_list_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE task_list_id_seq OWNER TO postgres;

--
-- Name: task_list_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE task_list_id_seq OWNED BY task_list.id;


--
-- Name: tokens; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE tokens (
    id integer NOT NULL,
    host_id integer NOT NULL,
    token character varying(45) NOT NULL
);


ALTER TABLE tokens OWNER TO postgres;

--
-- Name: tokens_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE tokens_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE tokens_id_seq OWNER TO postgres;

--
-- Name: tokens_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE tokens_id_seq OWNED BY tokens.id;


--
-- Name: trigger_descriptions; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE trigger_descriptions (
    id integer NOT NULL,
    trigger_name character varying(45) NOT NULL,
    trigger_description character varying(450) NOT NULL
);


ALTER TABLE trigger_descriptions OWNER TO postgres;

--
-- Name: trigger_descriptions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE trigger_descriptions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE trigger_descriptions_id_seq OWNER TO postgres;

--
-- Name: trigger_descriptions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE trigger_descriptions_id_seq OWNED BY trigger_descriptions.id;


--
-- Name: trigger_events; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE trigger_events (
    id integer NOT NULL,
    trigger_descriptions_id integer NOT NULL,
    task_descriptions_id integer NOT NULL,
    value_mask character varying(45) DEFAULT '%'::character varying NOT NULL,
    enabled boolean DEFAULT false NOT NULL
);


ALTER TABLE trigger_events OWNER TO postgres;

--
-- Name: trigger_events_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE trigger_events_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE trigger_events_id_seq OWNER TO postgres;

--
-- Name: trigger_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE trigger_events_id_seq OWNED BY trigger_events.id;


--
-- Name: vulnerabilities; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE vulnerabilities (
    id integer NOT NULL,
    port_data_id integer NOT NULL,
    vulnerability_descriptions_id integer NOT NULL,
    details character varying(450) DEFAULT ''::character varying NOT NULL
);


ALTER TABLE vulnerabilities OWNER TO postgres;

--
-- Name: vulnerabilities_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE vulnerabilities_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE vulnerabilities_id_seq OWNER TO postgres;

--
-- Name: vulnerabilities_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE vulnerabilities_id_seq OWNED BY vulnerabilities.id;


--
-- Name: vulnerability_descriptions; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE vulnerability_descriptions (
    id integer NOT NULL,
    description character varying(45) NOT NULL
);


ALTER TABLE vulnerability_descriptions OWNER TO postgres;

--
-- Name: vulnerability_descriptions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE vulnerability_descriptions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE vulnerability_descriptions_id_seq OWNER TO postgres;

--
-- Name: vulnerability_descriptions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE vulnerability_descriptions_id_seq OWNED BY vulnerability_descriptions.id;


--
-- Name: websites; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE websites (
    id integer NOT NULL,
    port_data_id integer NOT NULL,
    html_title character varying(45) NOT NULL,
    html_body text NOT NULL,
    screenshot text NOT NULL
);


ALTER TABLE websites OWNER TO postgres;

--
-- Name: websites_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE websites_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE websites_id_seq OWNER TO postgres;

--
-- Name: websites_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE websites_id_seq OWNED BY websites.id;


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY domain_credentials ALTER COLUMN id SET DEFAULT nextval('domain_credentials_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY domain_credentials_map ALTER COLUMN id SET DEFAULT nextval('domain_credentials_map_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY domain_groups ALTER COLUMN id SET DEFAULT nextval('domain_groups_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY domain_sub_groups ALTER COLUMN id SET DEFAULT nextval('domain_sub_groups_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY domain_user_group_map ALTER COLUMN id SET DEFAULT nextval('domain_user_group_map_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY domains ALTER COLUMN id SET DEFAULT nextval('domains_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY exploit_logs ALTER COLUMN id SET DEFAULT nextval('exploit_logs_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY footprints ALTER COLUMN id SET DEFAULT nextval('footprints_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY host_data ALTER COLUMN id SET DEFAULT nextval('host_data_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY local_credentials ALTER COLUMN id SET DEFAULT nextval('local_credentials_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY local_credentials_map ALTER COLUMN id SET DEFAULT nextval('local_credentials_map_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY net_ranges ALTER COLUMN id SET DEFAULT nextval('net_ranges_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY port_data ALTER COLUMN id SET DEFAULT nextval('port_data_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY ports_to_scan ALTER COLUMN id SET DEFAULT nextval('ports_to_scan_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY scope ALTER COLUMN id SET DEFAULT nextval('scope_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY task_categories ALTER COLUMN id SET DEFAULT nextval('task_categories_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY task_descriptions ALTER COLUMN id SET DEFAULT nextval('task_descriptions_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY task_list ALTER COLUMN id SET DEFAULT nextval('task_list_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY tokens ALTER COLUMN id SET DEFAULT nextval('tokens_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY trigger_descriptions ALTER COLUMN id SET DEFAULT nextval('trigger_descriptions_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY trigger_events ALTER COLUMN id SET DEFAULT nextval('trigger_events_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY vulnerabilities ALTER COLUMN id SET DEFAULT nextval('vulnerabilities_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY vulnerability_descriptions ALTER COLUMN id SET DEFAULT nextval('vulnerability_descriptions_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY websites ALTER COLUMN id SET DEFAULT nextval('websites_id_seq'::regclass);


--
-- Data for Name: domain_credentials; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY domain_credentials (id, footprint_id, domain, username, cleartext_password, verified, lm_hash, ntlm_hash, valid) FROM stdin;
\.


--
-- Name: domain_credentials_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('domain_credentials_id_seq', 1, false);


--
-- Data for Name: domain_credentials_map; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY domain_credentials_map (id, footprint_id, host_data_id, domain_credentials_id, valid, psexec_failed, dgu_failed) FROM stdin;
\.


--
-- Name: domain_credentials_map_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('domain_credentials_map_id_seq', 1, false);


--
-- Data for Name: domain_groups; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY domain_groups (id, footprint_id, domain_id, group_name, users_gathered) FROM stdin;
\.


--
-- Name: domain_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('domain_groups_id_seq', 1, false);


--
-- Data for Name: domain_sub_groups; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY domain_sub_groups (id, parent_group_id, child_group_id) FROM stdin;
1	2	7
2	21	56
3	1	21
4	1	19
5	2	22
6	3	23
7	33	34
8	33	24
9	33	21
10	33	20
11	33	19
12	33	18
13	33	17
14	3	22
15	57	77
16	57	75
17	58	78
18	59	79
19	89	90
20	89	80
21	89	77
22	89	76
23	89	75
24	89	74
25	89	73
26	113	133
27	113	131
28	114	134
29	115	135
30	145	146
31	145	136
32	145	133
33	145	132
34	145	131
35	145	130
36	145	129
37	169	189
38	169	187
39	170	190
40	171	191
41	201	202
42	201	192
43	201	189
44	201	188
45	201	187
46	201	186
47	201	185
48	225	245
49	225	243
50	226	246
51	227	247
52	257	258
53	257	248
54	257	245
55	257	244
56	257	243
57	257	242
58	257	241
59	283	303
60	313	314
61	313	304
62	313	301
63	313	300
64	313	299
65	313	298
66	313	297
67	281	301
68	281	299
69	282	302
70	339	338
71	339	345
72	339	346
73	339	347
74	339	348
75	339	349
76	339	351
77	339	352
78	339	360
79	339	361
80	339	362
81	339	363
82	339	364
83	339	365
84	339	417
85	339	418
86	339	419
87	340	338
88	340	345
89	340	346
90	340	347
91	340	348
92	340	349
93	340	351
94	340	352
95	340	360
96	340	361
97	340	362
98	340	363
99	340	364
100	340	365
101	340	417
102	340	418
103	340	419
104	341	338
105	341	345
106	341	346
107	341	347
108	341	348
109	341	349
110	341	351
111	341	352
112	341	360
113	341	361
114	341	362
115	341	363
116	341	364
117	341	365
118	341	417
119	341	418
120	341	419
121	343	338
122	343	345
123	343	346
124	343	347
125	343	348
126	343	349
127	343	351
128	343	352
129	343	360
130	343	361
131	343	362
132	343	363
133	343	364
134	343	365
135	343	417
136	343	418
137	343	419
138	347	338
139	347	345
140	347	346
141	347	347
142	347	348
143	347	349
144	347	351
145	347	352
146	347	360
147	347	361
148	347	362
149	347	363
150	347	364
151	347	365
152	347	417
153	347	418
154	347	419
155	338	347
156	337	351
157	474	470
158	480	471
159	617	613
160	623	614
161	632	621
162	632	633
163	870	866
164	876	867
165	885	874
166	885	886
167	944	874
168	947	874
169	744	746
170	744	745
171	744	742
172	744	741
173	744	737
174	751	741
175	752	738
176	753	739
\.


--
-- Name: domain_sub_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('domain_sub_groups_id_seq', 176, true);


--
-- Data for Name: domain_user_group_map; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY domain_user_group_map (id, domain_credentials_id, domain_group_id) FROM stdin;
\.


--
-- Name: domain_user_group_map_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('domain_user_group_map_id_seq', 1, false);


--
-- Data for Name: domains; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY domains (id, footprint_id, domain_name, info_gathered, hashes_extracted) FROM stdin;
\.


--
-- Name: domains_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('domains_id_seq', 1, false);


--
-- Data for Name: exploit_logs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY exploit_logs (id, host_data_id, vulnerability_description_id, log) FROM stdin;
\.


--
-- Name: exploit_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('exploit_logs_id_seq', 1, false);


--
-- Data for Name: footprints; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY footprints (id, footprint_name) FROM stdin;
\.


--
-- Name: footprints_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('footprints_id_seq', 1, false);


--
-- Data for Name: host_data; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY host_data (id, footprint_id, ip_address, host_name, computer_name, os, architecture, system_language, domain, is_dc, successful_info_gather) FROM stdin;
\.


--
-- Name: host_data_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('host_data_id_seq', 1, false);


--
-- Data for Name: local_credentials; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY local_credentials (id, host_data_id, username, cleartext_password, lm_hash, ntlm_hash) FROM stdin;
\.


--
-- Name: local_credentials_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('local_credentials_id_seq', 1, false);


--
-- Data for Name: local_credentials_map; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY local_credentials_map (id, host_data_id, local_credentials_id, valid) FROM stdin;
\.


--
-- Name: local_credentials_map_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('local_credentials_map_id_seq', 1, false);


--
-- Data for Name: net_ranges; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY net_ranges (id, footprint_id, net_range) FROM stdin;
\.


--
-- Name: net_ranges_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('net_ranges_id_seq', 1, false);


--
-- Data for Name: port_data; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY port_data (id, host_data_id, port_number) FROM stdin;
\.


--
-- Name: port_data_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('port_data_id_seq', 1, false);


--
-- Data for Name: ports_to_scan; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY ports_to_scan (id, type_id, port_number) FROM stdin;
1	1	22
2	1	445
3	2	22
4	2	445
5	2	80
6	2	443
7	\N	80
10	2	8443
15	2	21
16	2	135
17	2	1433
18	2	3306
19	2	3389
20	2	5800
21	2	5900
22	2	8080
24	1	80
\.


--
-- Name: ports_to_scan_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('ports_to_scan_id_seq', 24, true);


--
-- Data for Name: scope; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY scope (id, footprint_id, item_type, item_value) FROM stdin;
\.


--
-- Name: scope_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('scope_id_seq', 1, false);


--
-- Data for Name: task_categories; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY task_categories (id, category, description, position_id) FROM stdin;
1	Host Enumeration	Identify hosts by querying standard infrastructure	1
2	Fingerprinting	Gather information about hosts, such as host names and open ports	2
3	Vulnerability Scanning	Scan hosts for common vulnerabilities	3
4	Vulnerability Exploitation	Exploit vulnerabilities and gather information such as domain credentials and impersonation tokens	4
5	Network Pivoting	Reuse credentials and tokens across the domain in an attempt to gain access to domain controllers	5
6	Domain Enumeration	Gathers and maps domain users and groups	6
\.


--
-- Name: task_categories_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('task_categories_id_seq', 6, true);


--
-- Data for Name: task_descriptions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY task_descriptions (id, task_categories_id, task_name, description, file_name, uses_metasploit, is_recursive, enabled) FROM stdin;
1	1	Add Local IP	Portscan the class C your IP address falls in	plugins.host_enumeration.add_local_ip	f	f	t
5	1	Add Local Nameservers	...	plugins.host_enumeration.add_local_nameservers	f	f	t
7	3	Check MS08-067	...	plugins.vuln_scanning.ms08_067	f	f	t
8	4	Exploit MS08-067	...	plugins.vuln_exploits.exploit_ms08_067	t	f	t
9	5	Pivot on local accounts	...	plugins.pivoting.retry_local_accounts	f	t	f
10	5	Local account login with PsExec	...	plugins.pivoting.psexec_local_account	t	f	f
12	3	Check Weak SQL Creds	...	plugins.vuln_scanning.weak_sql_creds	f	f	t
13	4	Exploit Weak SQL Creds	...	plugins.vuln_exploits.exploit_weak_sql_creds	t	f	t
14	3	Check for weak Tomcat creds	...	plugins.vuln_scanning.weak_tomcat_creds	f	f	t
15	4	Exploit Weak Tomcat Creds	...	plugins.vuln_exploits.exploit_weak_tomcat_creds	t	f	t
19	5	Verify domain credentials	...	plugins.pivoting.verify_domain_credentials	f	t	t
25	1	Zone Transfer Assigned Domain	...	plugins.host_enumeration.zone_transfer_assigned_domain	f	f	t
18	2	Portscan scoped range	...	plugins.footprinting.portscan_scoped_range	f	f	t
11	2	Portscan scoped host	...	plugins.footprinting.portscan_scoped_host	f	f	t
6	2	Screenshot Website	...	plugins.footprinting.screenshot_website	f	f	t
16	5	Check domain credentials for remote access	...	plugins.pivoting.retry_domain_accounts	f	t	t
17	5	Domain account login with PsExec	...	plugins.pivoting.psexec_domain_account	f	f	t
3	2	Portscan Net Range	...	plugins.footprinting.portscan_net_range	f	f	t
23	2	Net Range DNS Lookups	...	plugins.footprinting.net_range_dns_lookup	f	f	t
21	6	Extract domain hashes	...	plugins.domain_enumeration.extract_domain_hashes	f	t	t
22	6	Bruteforce domain hashes	Run john with the following lists\n - Short list of weak passwords, ie Password1, January2016 etc\n - Passwords recovered with Mimikatz\n - Previously cracked passwords\n\nRun john again for 5 minutes\n\nThen run john --show, and save the output	plugins.domain_enumeration.bruteforce_ntlm_hashes	f	f	t
20	6	Gather domain groups	List and save the domain groups	plugins.domain_enumeration.enumerate_groups	f	t	t
26	6	Gather domain users	Gather domain users for a group	plugins.domain_enumeration.enumerate_users	f	t	t
27	2	Query MSSQL Discovery service	Check the discovery service on UDP port 1434 for info on sql servers running on high ports	plugins.footprinting.query_mssql_discovery_service	f	f	t
2	2	Portscan Host	...	plugins.footprinting.portscan_host	f	f	f
4	2	Host DNS Lookup	...	plugins.footprinting.host_dns_lookup	f	f	f
24	2	Scoped Range DNS Lookups	...	plugins.footprinting.scoped_range_dns_lookup	f	f	t
\.


--
-- Name: task_descriptions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('task_descriptions_id_seq', 27, true);


--
-- Data for Name: task_list; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY task_list (id, footprint_id, task_descriptions_id, item_identifier, in_progress, completed, log) FROM stdin;
\.


--
-- Name: task_list_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('task_list_id_seq', 1, false);


--
-- Data for Name: tokens; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY tokens (id, host_id, token) FROM stdin;
\.


--
-- Name: tokens_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('tokens_id_seq', 1, false);


--
-- Data for Name: trigger_descriptions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY trigger_descriptions (id, trigger_name, trigger_description) FROM stdin;
1	New host found	...
2	Open port found	...
3	Net range found	...
4	Vuln found	...
5	Local creds found	...
6	New scoped host	...
7	New scoped range	...
8	Domain creds found	...
9	Domain creds verified	...
10	New domain found	...
11	Domain hashes extracted	...
12	SQL Service on found on high port	...
\.


--
-- Name: trigger_descriptions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('trigger_descriptions_id_seq', 12, true);


--
-- Data for Name: trigger_events; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY trigger_events (id, trigger_descriptions_id, task_descriptions_id, value_mask, enabled) FROM stdin;
1	1	2	%	f
2	1	4	%	f
3	2	6	80	t
4	3	3	%	t
5	2	7	445	t
6	4	8	MS08-067	t
7	5	10	%	t
8	6	11	%	t
9	2	12	1433	t
10	4	13	Weak MSSQL Creds	t
11	2	14	8080	t
12	4	15	Weak Tomcat Creds	t
13	9	17	%	t
14	7	18	%	t
15	8	19	%	t
16	2	6	8080	t
17	2	6	443	t
18	2	6	8443	t
19	11	22	%	t
20	3	23	%	t
21	7	24	%	t
22	2	14	8443	t
23	3	27	%	t
24	12	12	%	t
\.


--
-- Name: trigger_events_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('trigger_events_id_seq', 24, true);


--
-- Data for Name: vulnerabilities; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY vulnerabilities (id, port_data_id, vulnerability_descriptions_id, details) FROM stdin;
\.


--
-- Name: vulnerabilities_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('vulnerabilities_id_seq', 1, false);


--
-- Data for Name: vulnerability_descriptions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY vulnerability_descriptions (id, description) FROM stdin;
1	MS08-067
2	Weak MSSQL Creds
3	Weak Tomcat Creds
4	PsExec
\.


--
-- Name: vulnerability_descriptions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('vulnerability_descriptions_id_seq', 4, true);


--
-- Data for Name: websites; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY websites (id, port_data_id, html_title, html_body, screenshot) FROM stdin;
\.


--
-- Name: websites_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('websites_id_seq', 1, false);


--
-- Name: domain_credentials_map_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY domain_credentials_map
    ADD CONSTRAINT domain_credentials_map_pkey PRIMARY KEY (id);


--
-- Name: domain_credentials_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY domain_credentials
    ADD CONSTRAINT domain_credentials_pkey PRIMARY KEY (id);


--
-- Name: domain_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY domain_groups
    ADD CONSTRAINT domain_groups_pkey PRIMARY KEY (id);


--
-- Name: domain_sub_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY domain_sub_groups
    ADD CONSTRAINT domain_sub_groups_pkey PRIMARY KEY (id);


--
-- Name: domain_user_group_map_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY domain_user_group_map
    ADD CONSTRAINT domain_user_group_map_pkey PRIMARY KEY (id);


--
-- Name: domains_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY domains
    ADD CONSTRAINT domains_pkey PRIMARY KEY (id);


--
-- Name: exploit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY exploit_logs
    ADD CONSTRAINT exploit_logs_pkey PRIMARY KEY (id);


--
-- Name: footprints_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY footprints
    ADD CONSTRAINT footprints_pkey PRIMARY KEY (id);


--
-- Name: host_data_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY host_data
    ADD CONSTRAINT host_data_pkey PRIMARY KEY (id);


--
-- Name: local_credentials_map_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY local_credentials_map
    ADD CONSTRAINT local_credentials_map_pkey PRIMARY KEY (id);


--
-- Name: local_credentials_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY local_credentials
    ADD CONSTRAINT local_credentials_pkey PRIMARY KEY (id);


--
-- Name: net_ranges_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY net_ranges
    ADD CONSTRAINT net_ranges_pkey PRIMARY KEY (id);


--
-- Name: port_data_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY port_data
    ADD CONSTRAINT port_data_pkey PRIMARY KEY (id);


--
-- Name: ports_to_scan_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY ports_to_scan
    ADD CONSTRAINT ports_to_scan_pkey PRIMARY KEY (id);


--
-- Name: scope_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY scope
    ADD CONSTRAINT scope_pkey PRIMARY KEY (id);


--
-- Name: task_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY task_categories
    ADD CONSTRAINT task_categories_pkey PRIMARY KEY (id);


--
-- Name: task_descriptions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY task_descriptions
    ADD CONSTRAINT task_descriptions_pkey PRIMARY KEY (id);


--
-- Name: task_list_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY task_list
    ADD CONSTRAINT task_list_pkey PRIMARY KEY (id);


--
-- Name: tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY tokens
    ADD CONSTRAINT tokens_pkey PRIMARY KEY (id);


--
-- Name: trigger_descriptions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY trigger_descriptions
    ADD CONSTRAINT trigger_descriptions_pkey PRIMARY KEY (id);


--
-- Name: trigger_events_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY trigger_events
    ADD CONSTRAINT trigger_events_pkey PRIMARY KEY (id);


--
-- Name: vulnerabilities_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY vulnerabilities
    ADD CONSTRAINT vulnerabilities_pkey PRIMARY KEY (id);


--
-- Name: vulnerability_descriptions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY vulnerability_descriptions
    ADD CONSTRAINT vulnerability_descriptions_pkey PRIMARY KEY (id);


--
-- Name: websites_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY websites
    ADD CONSTRAINT websites_pkey PRIMARY KEY (id);


--
-- Name: domain_credentials_footprint_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX domain_credentials_footprint_id ON domain_credentials USING btree (footprint_id);


--
-- Name: domain_credentials_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX domain_credentials_id ON domain_credentials USING btree (id);


--
-- Name: domain_credentials_map_domain_credentials_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX domain_credentials_map_domain_credentials_id ON domain_credentials_map USING btree (domain_credentials_id);


--
-- Name: domain_credentials_map_footprint_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX domain_credentials_map_footprint_id ON domain_credentials_map USING btree (footprint_id);


--
-- Name: domain_credentials_map_host_data_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX domain_credentials_map_host_data_id ON domain_credentials_map USING btree (host_data_id);


--
-- Name: domain_credentials_map_valid; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX domain_credentials_map_valid ON domain_credentials_map USING btree (valid);


--
-- Name: host_data_footprint_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX host_data_footprint_id ON host_data USING btree (footprint_id);


--
-- Name: host_data_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX host_data_id ON host_data USING btree (id);


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

