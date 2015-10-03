grant all on *.* to 'root'@'%';

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='TRADITIONAL,ALLOW_INVALID_DATES';

CREATE SCHEMA IF NOT EXISTS `autodane` DEFAULT CHARACTER SET latin1 ;
USE `autodane` ;

-- -----------------------------------------------------
-- Table `autodane`.`cred_host_map`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `autodane`.`cred_host_map` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `host_data_id` INT(11) NOT NULL,
  `domain_creds_id` INT(11) NOT NULL,
  `successful` BIT(1) NOT NULL DEFAULT b'0',
  `login_count` int(11) DEFAULT '0',
  PRIMARY KEY (`id`))
ENGINE = InnoDB
AUTO_INCREMENT = 21
DEFAULT CHARACTER SET = latin1;


-- -----------------------------------------------------
-- Table `autodane`.`domain_creds`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `autodane`.`domain_creds` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `footprint_id` INT(11) NOT NULL,
  `domain_name` VARCHAR(45) NOT NULL DEFAULT '',
  `is_da` BIT(1) NOT NULL DEFAULT b'0',
  `username` VARCHAR(45) NOT NULL DEFAULT '',
  `cleartext_password` VARCHAR(150) NOT NULL DEFAULT '',
  `lm_hash` VARCHAR(150) NOT NULL DEFAULT '',
  `ntlm_hash` VARCHAR(150) NOT NULL DEFAULT '',
  `http_ntlm_hash` VARCHAR(250) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`))
ENGINE = InnoDB
AUTO_INCREMENT = 5
DEFAULT CHARACTER SET = latin1;


-- -----------------------------------------------------
-- Table `autodane`.`domains`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `autodane`.`domains` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `footprint_id` INT(11) NOT NULL,
  `domain_name` VARCHAR(45) NULL DEFAULT NULL,
  `zone_transfer_attempted` BIT(1) NOT NULL DEFAULT b'0',
  PRIMARY KEY (`id`))
ENGINE = InnoDB
AUTO_INCREMENT = 2
DEFAULT CHARACTER SET = latin1;


-- -----------------------------------------------------
-- Table `autodane`.`footprints`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `autodane`.`footprints` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `footprint_name` VARCHAR(45) NOT NULL,
  `10_range_position` VARCHAR(45) NOT NULL DEFAULT '10.0.0.0/16',
  `172_range_position` VARCHAR(45) NOT NULL DEFAULT '172.16.0.0.0/16',
  `192_range_position` VARCHAR(45) NOT NULL DEFAULT '192.168.0.0/16',
  `msfrpc_pass` VARCHAR(45) NULL DEFAULT NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB
AUTO_INCREMENT = 2
DEFAULT CHARACTER SET = latin1;


-- -----------------------------------------------------
-- Table `autodane`.`host_data`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `autodane`.`host_data` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `footprint_id` INT(11) NOT NULL,
  `ip_address` VARCHAR(45) NOT NULL,
  `host_name` VARCHAR(45) NOT NULL DEFAULT '',
  `is_dc` BIT(1) NOT NULL DEFAULT b'0',
  `dns_lookup_done` BIT(1) NULL DEFAULT b'0',
  `port_scan_done` BIT(1) NULL DEFAULT b'0',
  `creds_gathered` DATETIME NULL DEFAULT '1900-01-01 00:00:00',
  `cred_gather_successful` BIT(1) NULL DEFAULT b'0',
  `domain_creds_id` INT(11) NULL DEFAULT NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB
AUTO_INCREMENT = 8
DEFAULT CHARACTER SET = latin1;


-- -----------------------------------------------------
-- Table `autodane`.`ports`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `autodane`.`ports` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `host_data_id` INT(11) NOT NULL,
  `port_num` INT(11) NOT NULL,
  `vuln_checked` BIT(1) NOT NULL DEFAULT b'0',
  `vulnerable` BIT(1) NOT NULL DEFAULT b'0',
  `shell` BIT(1) NOT NULL DEFAULT b'0',
  `notes` VARCHAR(100) NOT NULL DEFAULT '',
  `vulnerability_name` VARCHAR(45) NOT NULL DEFAULT '',
  `http_title_checked` BIT(1) NOT NULL DEFAULT b'0',
  `http_title` VARCHAR(250) NOT NULL DEFAULT '',
  `exploited` DATETIME NULL DEFAULT '1900-01-01 00:00:00',
  PRIMARY KEY (`id`))
ENGINE = InnoDB
AUTO_INCREMENT = 14
DEFAULT CHARACTER SET = latin1;


-- -----------------------------------------------------
-- Table `autodane`.`ranges`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `autodane`.`ranges` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `footprint_id` INT(11) NOT NULL,
  `net_range` VARCHAR(45) NOT NULL,
  `dns_lookups_done` BIT(1) NOT NULL DEFAULT b'0',
  `port_scans_done` BIT(1) NOT NULL DEFAULT b'0',
  PRIMARY KEY (`id`))
ENGINE = InnoDB
AUTO_INCREMENT = 2
DEFAULT CHARACTER SET = latin1;

USE `autodane` ;

-- -----------------------------------------------------
-- procedure addDomain
-- -----------------------------------------------------

DELIMITER $$
USE `autodane`$$
CREATE DEFINER=`root`@`localhost` PROCEDURE `addDomain`(in _footprint_id int, in _domain_name varchar(45))
BEGIN
	if (select count(*) from domains where footprint_id = _footprint_id and domain_name = _domain_name) = 0 then
		insert into domains (footprint_id, domain_name) values (_footprint_id, _domain_name);
	end if;
END$$

DELIMITER ;

-- -----------------------------------------------------
-- procedure addDomainCreds
-- -----------------------------------------------------

DELIMITER $$
USE `autodane`$$
CREATE DEFINER=`root`@`%` PROCEDURE `addDomainCreds`(in _fp_id int, in _dn_n varchar(45), in _un varchar(45), in _ct_pw varchar(150), in _lm_h varchar(150), in _ntlm_h varchar(150), in http_ntlm_h varchar(150))
BEGIN
	if (select count(*) from domain_creds where footprint_id = _fp_id and domain_name = _dn_n and username = _un) = 0 then
		insert into domain_creds (footprint_id, domain_name, username) values (_fp_id, _dn_n, _un);
	end if;

	if (_ct_pw != "") then
		update domain_creds set cleartext_password = _ct_pw where
		footprint_id = _fp_id and domain_name = _dn_n and username = _un;
	end if;
END$$

DELIMITER ;

-- -----------------------------------------------------
-- procedure addIP
-- -----------------------------------------------------

DELIMITER $$
USE `autodane`$$
CREATE DEFINER=`root`@`localhost` PROCEDURE `addIP`(in _footprint_id int, _ip_address varchar(45), in is_dc bit)
BEGIN
	if (select count(*) from host_data where footprint_id = _footprint_id and ip_address = _ip_address) = 0 then
		insert into host_data (footprint_id, ip_address, is_dc) values (_footprint_id, _ip_address, is_dc);
	end if;
END$$

DELIMITER ;

-- -----------------------------------------------------
-- procedure addLoginAttemptResult
-- -----------------------------------------------------

DELIMITER $$
USE `autodane`$$
CREATE DEFINER=`root`@`%` PROCEDURE `addLoginAttemptResult`(in _host_data_id int, in _domain_creds_id int, in _success bit)
BEGIN
    if (select count(*) from cred_host_map where host_data_id = _host_data_id and domain_creds_id = _domain_creds_id) = 0 then
	insert into cred_host_map 
		(host_data_id, domain_creds_id, successful) values 
		(_host_data_id, _domain_creds_id, _success);
    end if;

    update cred_host_map set login_count = login_count+1 where
    host_data_id = _host_data_id and 
    domain_creds_id = _domain_creds_id;
END$$

DELIMITER ;

-- -----------------------------------------------------
-- procedure addPort
-- -----------------------------------------------------

DELIMITER $$
USE `autodane`$$
CREATE DEFINER=`root`@`localhost` PROCEDURE `addPort`(in _ip_address varchar(45), in _port_num int)
BEGIN
	if (select count(*)from host_data h join ports p on h.id = p.host_data_id where h.ip_address = _ip_address and p.port_num = _port_num)= 0 then
		insert into ports (host_data_id, port_num) values ((select id from host_data where ip_address = _ip_address limit 1), _port_num);
	end if;
END$$

DELIMITER ;

-- -----------------------------------------------------
-- procedure addRange
-- -----------------------------------------------------

DELIMITER $$
USE `autodane`$$
CREATE DEFINER=`root`@`localhost` PROCEDURE `addRange`(in _footprint_id int, in _net_range varchar(45))
BEGIN
	if (select count(*) from ranges where footprint_id = _footprint_id and net_range = _net_range) = 0 then
		insert into ranges (footprint_id, net_range) values (_footprint_id, _net_range);
	end if;
END$$

DELIMITER ;

-- -----------------------------------------------------
-- procedure createFootprint
-- -----------------------------------------------------

DELIMITER $$
USE `autodane`$$
CREATE DEFINER=`root`@`localhost` PROCEDURE `createFootprint`(in _footprint_name varchar(45))
BEGIN
	if (select count(*) from footprints where footprint_name = _footprint_name) = 0 then
		insert into footprints (footprint_name) values (_footprint_name);
	end if;

	select id from footprints where footprint_name = _footprint_name;
END$$

DELIMITER ;

-- -----------------------------------------------------
-- procedure getHostToLogInTo
-- -----------------------------------------------------

DELIMITER $$
USE `autodane`$$
CREATE DEFINER=`root`@`%` PROCEDURE `getHostToLogInTo`(in _footprint_id int)
BEGIN
	select
		hd.id as 'host_data_id', hd.ip_address, dc.id as 'domain_creds_id', dc.domain_name, dc.username, dc.cleartext_password
	from
		host_data hd 
		join domain_creds dc on hd.footprint_id = dc.footprint_id
		join ports p on hd.id = p.host_data_id
	where 
		hd.footprint_id = _footprint_id and
		p.port_num = 445 and
		hd.id not in (select host_data_id from cred_host_map where host_data_id = hd.id and domain_creds_id = dc.id) and
		dc.cleartext_password != ""
	limit
		1;
END$$

DELIMITER ;

-- -----------------------------------------------------
-- procedure getVulnerableToMS08067
-- -----------------------------------------------------

DELIMITER $$
USE `autodane`$$
CREATE DEFINER=`root`@`%` PROCEDURE `getVulnerableToMS08067`(in _footprint_id int)
BEGIN
	select 
		hd.ip_address, p.id, p.port_num
	from
		host_data hd
		join ports p on hd.id = p.host_data_id
	where
		hd.footprint_id = _footprint_id and
		p.shell = 1 and
		p.port_num = 445 and
		p.exploited = '1900-01-01 00:00:00'
	order by exploited asc limit 1;
END$$

DELIMITER ;

-- -----------------------------------------------------
-- procedure getVulnerableWeakSqlCreds
-- -----------------------------------------------------

DELIMITER $$
USE `autodane`$$
CREATE DEFINER=`root`@`%` PROCEDURE `getVulnerableWeakSqlCreds`(in _footprint_id int)
BEGIN
	select 
		hd.ip_address, p.id, p.port_num, p.notes
	from
		host_data hd
		join ports p on hd.id = p.host_data_id
	where
		hd.footprint_id = _footprint_id and
		p.shell = 1 and
		p.port_num = 1433 and 
		p.exploited = '1900-01-01 00:00:00'
	order by exploited asc limit 1;
END$$

DELIMITER ;

-- -----------------------------------------------------
-- procedure getVulnerableWeakTomcatCreds
-- -----------------------------------------------------

DELIMITER $$
USE `autodane`$$
CREATE DEFINER=`root`@`%` PROCEDURE `getVulnerableWeakTomcatCreds`(in _footprint_id int)
BEGIN
	select 
		hd.ip_address, p.id, p.port_num, p.notes
	from
		host_data hd
		join ports p on hd.id = p.host_data_id
	where
		hd.footprint_id = _footprint_id and
		p.shell = 1 and
		p.exploited = '1900-01-01 00:00:00' and
		p.vulnerability_name = 'Weak Tomcat Creds'
	order by exploited asc limit 1;
END$$

DELIMITER ;

-- -----------------------------------------------------
-- procedure report_pendingFootprinting
-- -----------------------------------------------------

DELIMITER $$
USE `autodane`$$
CREATE DEFINER=`root`@`localhost` PROCEDURE `report_pendingFootprinting`(in _footprint_id int)
BEGIN
	select "Pending Range DNS Lookups" as label, (select count(*) from ranges where footprint_id = _footprint_id and dns_lookups_done = 0) as val
	union select "Pending Range Port Scans", (select count(*) from ranges where footprint_id = _footprint_id and port_scans_done = 0) 
	union select "Pending Host DNS Lookups", (select count(*) from host_data where footprint_id = _footprint_id and dns_lookup_done = 0) 
	union select "Pending Host Port Scans", (select count(*) from host_data where footprint_id = _footprint_id and port_scan_done = 0) 
	union select "Pending HTML Title Checks", (select count(*) from host_data h join ports p on h.id = p.host_data_id where p.port_num in (80,443,8080,8081,8082,8083,8084,8085,8086,8087,8088,8089,8090,9090,9091,9092,9093,9094,9095,9096,9097,9098,9099) and h.footprint_id = _footprint_id and p.http_title_checked = 0);
END$$

DELIMITER ;

-- -----------------------------------------------------
-- procedure report_pendingVulnScanning
-- -----------------------------------------------------

DELIMITER $$
USE `autodane`$$
CREATE DEFINER=`root`@`localhost` PROCEDURE `report_pendingVulnScanning`(in _footprint_id int)
BEGIN
	select 
		p.port_num,
		count(p.port_num)
	from 
		host_data hd 
		join ports p on hd.id = p.host_data_id
	where
		hd.footprint_id = _footprint_id
		and vuln_checked = 0
	group by
		p.port_num;
END$$

DELIMITER ;

-- -----------------------------------------------------
-- procedure updatePortVulnerability
-- -----------------------------------------------------

DELIMITER $$
USE `autodane`$$
CREATE DEFINER=`root`@`localhost` PROCEDURE `updatePortVulnerability`(in _footprint_id int, in _ip_address varchar(45), in _port_num int, in _vuln_checked bit, in _vulnerable bit, in _shell bit, in _notes varchar(100), in _vulnerability_name varchar(45))
BEGIN
	update 
		ports 
	set 
		vuln_checked = _vuln_checked, 
		vulnerable = _vulnerable,
		shell = _shell, 
		notes = _notes, 
		vulnerability_name = _vulnerability_name 
	where 
		port_num = _port_num and 
		host_data_id = (select id from host_data where ip_address = _ip_address and footprint_id = _footprint_id limit 1);
END$$

DELIMITER ;

SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
