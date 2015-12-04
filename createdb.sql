CREATE DATABASE  IF NOT EXISTS `autodane` /*!40100 DEFAULT CHARACTER SET latin1 */;
USE `autodane`;
-- MySQL dump 10.13  Distrib 5.5.44, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: autodane
-- ------------------------------------------------------
-- Server version	5.5.44-0+deb8u1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `domain_credentials`
--

DROP TABLE IF EXISTS `domain_credentials`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `domain_credentials` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `footprint_id` int(11) NOT NULL,
  `domain` varchar(45) NOT NULL,
  `username` varchar(45) NOT NULL,
  `cleartext_password` varchar(45) NOT NULL DEFAULT '',
  `verified` bit(1) NOT NULL DEFAULT b'0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `domain_credentials`
--

LOCK TABLES `domain_credentials` WRITE;
/*!40000 ALTER TABLE `domain_credentials` DISABLE KEYS */;
/*!40000 ALTER TABLE `domain_credentials` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `domain_credentials_map`
--

DROP TABLE IF EXISTS `domain_credentials_map`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `domain_credentials_map` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `footprint_id` int(11) NOT NULL,
  `host_data_id` int(11) NOT NULL,
  `domain_credentials_id` int(11) NOT NULL,
  `valid` bit(1) NOT NULL DEFAULT b'0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `domain_credentials_map`
--

LOCK TABLES `domain_credentials_map` WRITE;
/*!40000 ALTER TABLE `domain_credentials_map` DISABLE KEYS */;
/*!40000 ALTER TABLE `domain_credentials_map` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `domains`
--

DROP TABLE IF EXISTS `domains`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `domains` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `footprint_id` int(11) NOT NULL,
  `domain_name` varchar(45) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `domains`
--

LOCK TABLES `domains` WRITE;
/*!40000 ALTER TABLE `domains` DISABLE KEYS */;
/*!40000 ALTER TABLE `domains` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `exploit_logs`
--

DROP TABLE IF EXISTS `exploit_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `exploit_logs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `host_data_id` int(11) NOT NULL,
  `vulnerability_description_id` int(11) NOT NULL,
  `log` mediumtext NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `exploit_logs`
--

LOCK TABLES `exploit_logs` WRITE;
/*!40000 ALTER TABLE `exploit_logs` DISABLE KEYS */;
/*!40000 ALTER TABLE `exploit_logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `footprints`
--

DROP TABLE IF EXISTS `footprints`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `footprints` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `footprint_name` varchar(45) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `footprints`
--

LOCK TABLES `footprints` WRITE;
/*!40000 ALTER TABLE `footprints` DISABLE KEYS */;
/*!40000 ALTER TABLE `footprints` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `host_data`
--

DROP TABLE IF EXISTS `host_data`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `host_data` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `footprint_id` int(11) NOT NULL,
  `ip_address` varchar(45) NOT NULL,
  `host_name` varchar(45) NOT NULL DEFAULT '',
  `computer_name` varchar(45) NOT NULL DEFAULT '',
  `os` varchar(100) NOT NULL DEFAULT '',
  `architecture` varchar(45) NOT NULL DEFAULT '',
  `system_language` varchar(45) NOT NULL DEFAULT '',
  `domain` varchar(45) NOT NULL DEFAULT '',
  `is_dc` bit(1) NOT NULL DEFAULT b'0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `host_data`
--

LOCK TABLES `host_data` WRITE;
/*!40000 ALTER TABLE `host_data` DISABLE KEYS */;
/*!40000 ALTER TABLE `host_data` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `local_credentials`
--

DROP TABLE IF EXISTS `local_credentials`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `local_credentials` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `host_data_id` int(11) NOT NULL,
  `username` varchar(45) NOT NULL,
  `cleartext_password` varchar(100) NOT NULL DEFAULT '',
  `lm_hash` varchar(45) NOT NULL DEFAULT '',
  `ntlm_hash` varchar(45) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `local_credentials`
--

LOCK TABLES `local_credentials` WRITE;
/*!40000 ALTER TABLE `local_credentials` DISABLE KEYS */;
/*!40000 ALTER TABLE `local_credentials` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `local_credentials_map`
--

DROP TABLE IF EXISTS `local_credentials_map`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `local_credentials_map` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `host_data_id` int(11) DEFAULT NULL,
  `local_credentials_id` int(11) DEFAULT NULL,
  `valid` bit(1) DEFAULT b'0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `local_credentials_map`
--

LOCK TABLES `local_credentials_map` WRITE;
/*!40000 ALTER TABLE `local_credentials_map` DISABLE KEYS */;
/*!40000 ALTER TABLE `local_credentials_map` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `net_ranges`
--

DROP TABLE IF EXISTS `net_ranges`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `net_ranges` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `footprint_id` int(11) NOT NULL,
  `net_range` varchar(45) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `net_ranges`
--

LOCK TABLES `net_ranges` WRITE;
/*!40000 ALTER TABLE `net_ranges` DISABLE KEYS */;
/*!40000 ALTER TABLE `net_ranges` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `port_data`
--

DROP TABLE IF EXISTS `port_data`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `port_data` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `host_data_id` int(11) NOT NULL,
  `port_number` int(11) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `port_data`
--

LOCK TABLES `port_data` WRITE;
/*!40000 ALTER TABLE `port_data` DISABLE KEYS */;
/*!40000 ALTER TABLE `port_data` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `scope`
--

DROP TABLE IF EXISTS `scope`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `scope` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `footprint_id` int(11) NOT NULL,
  `item_type` int(11) NOT NULL,
  `item_value` varchar(45) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `scope`
--

LOCK TABLES `scope` WRITE;
/*!40000 ALTER TABLE `scope` DISABLE KEYS */;
/*!40000 ALTER TABLE `scope` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `task_categories`
--

DROP TABLE IF EXISTS `task_categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `task_categories` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `category` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `task_categories`
--

LOCK TABLES `task_categories` WRITE;
/*!40000 ALTER TABLE `task_categories` DISABLE KEYS */;
INSERT INTO `task_categories` VALUES (1,'Host Enumeration'),(2,'Footprinting'),(3,'Vulnerability Scanning'),(4,'Vulnerability Exploitation'),(5,'Network Pivoting');
/*!40000 ALTER TABLE `task_categories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `task_descriptions`
--

DROP TABLE IF EXISTS `task_descriptions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `task_descriptions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `task_categories_id` int(11) DEFAULT NULL,
  `task_name` varchar(45) DEFAULT NULL,
  `description` varchar(45) DEFAULT NULL,
  `file_name` varchar(450) DEFAULT NULL,
  `uses_metasploit` bit(1) NOT NULL,
  `is_recursive` bit(1) NOT NULL DEFAULT b'0',
  `enabled` bit(1) NOT NULL DEFAULT b'0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `task_descriptions`
--

LOCK TABLES `task_descriptions` WRITE;
/*!40000 ALTER TABLE `task_descriptions` DISABLE KEYS */;
INSERT INTO `task_descriptions` VALUES (1,1,'Add Local IP','...','plugins.host_enumeration.add_local_ip','\0','\0','\0'),(2,2,'Portscan Host','...','plugins.footprinting.portscan_host','\0','\0','\0'),(3,2,'Portscan Net Range','...','plugins.footprinting.portscan_net_range','\0','\0',''),(4,2,'Host DNS Lookup','...','plugins.footprinting.host_dns_lookup','\0','\0','\0'),(5,1,'Add Local Nameservers','...','plugins.host_enumeration.add_local_nameservers','\0','\0','\0'),(6,2,'Screenshot Website','...','plugins.footprinting.screenshot_website','\0','\0',''),(7,3,'Check MS08-067','...','plugins.vuln_scanning.ms08_067','\0','\0',''),(8,4,'Exploit MS08-067','...','plugins.vuln_exploits.exploit_ms08_067','','\0',''),(9,5,'Pivot on local accounts','...','plugins.pivoting.retry_local_accounts','\0','',''),(10,5,'Local account login with PsExec','...','plugins.pivoting.psexec_local_account','','\0',''),(11,2,'Portscan scoped host','...','plugins.footprinting.portscan_scoped_host','\0','\0',''),(12,3,'Check Weak SQL Creds','...','plugins.vuln_scanning.weak_sql_creds','\0','\0',''),(13,4,'Exploit Weak SQL Creds','...','plugins.vuln_exploits.exploit_weak_sql_creds','','\0',''),(14,3,'Check for weak Tomcat creds','...','plugins.vuln_scanning.weak_tomcat_creds','\0','\0',''),(15,4,'Exploit Weak Tomcat Creds','...','plugins.vuln_exploits.exploit_weak_tomcat_creds','','\0',''),(16,5,'Pivot on domain accounts','...','plugins.pivoting.retry_domain_accounts','\0','',''),(17,5,'Domain account login with PsExec','...','plugins.pivoting.psexec_domain_account','','\0',''),(18,2,'Portscan scoped range','...','plugins.footprinting.portscan_scoped_range','\0','\0',''),(19,5,'Verify domain credentials','...','plugins.pivoting.verify_domain_credentials','\0','\0','');
/*!40000 ALTER TABLE `task_descriptions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `task_list`
--

DROP TABLE IF EXISTS `task_list`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `task_list` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `footprint_id` int(11) NOT NULL,
  `task_descriptions_id` int(11) NOT NULL,
  `item_identifier` int(11) NOT NULL DEFAULT '0',
  `in_progress` bit(1) NOT NULL DEFAULT b'0',
  `completed` bit(1) NOT NULL DEFAULT b'0',
  `log` mediumtext,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `task_list`
--

LOCK TABLES `task_list` WRITE;
/*!40000 ALTER TABLE `task_list` DISABLE KEYS */;
/*!40000 ALTER TABLE `task_list` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tokens`
--

DROP TABLE IF EXISTS `tokens`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tokens` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `host_id` int(11) NOT NULL,
  `token` varchar(45) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tokens`
--

LOCK TABLES `tokens` WRITE;
/*!40000 ALTER TABLE `tokens` DISABLE KEYS */;
/*!40000 ALTER TABLE `tokens` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `trigger_descriptions`
--

DROP TABLE IF EXISTS `trigger_descriptions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `trigger_descriptions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `trigger_name` varchar(45) NOT NULL,
  `trigger_description` varchar(450) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `trigger_descriptions`
--

LOCK TABLES `trigger_descriptions` WRITE;
/*!40000 ALTER TABLE `trigger_descriptions` DISABLE KEYS */;
INSERT INTO `trigger_descriptions` VALUES (1,'New host found','...'),(2,'Open port found','...'),(3,'Net range found','...'),(4,'Vuln found','...'),(5,'Local creds found','...'),(6,'New scoped host','...'),(7,'New scoped range','...'),(8,'Domain creds found','...'),(9,'Domain creds verified','...'),(10,'New domain found','...');
/*!40000 ALTER TABLE `trigger_descriptions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `trigger_events`
--

DROP TABLE IF EXISTS `trigger_events`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `trigger_events` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `trigger_descriptions_id` int(11) NOT NULL,
  `task_descriptions_id` int(11) NOT NULL,
  `value_mask` varchar(45) NOT NULL DEFAULT '%',
  `enabled` bit(1) NOT NULL DEFAULT b'0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `trigger_events`
--

LOCK TABLES `trigger_events` WRITE;
/*!40000 ALTER TABLE `trigger_events` DISABLE KEYS */;
INSERT INTO `trigger_events` VALUES (1,1,2,'%','\0'),(2,1,4,'%',''),(3,2,6,'80',''),(4,3,3,'%',''),(5,2,7,'445',''),(6,4,8,'MS08-067',''),(7,5,10,'%',''),(8,6,11,'%',''),(9,2,12,'1433',''),(10,4,13,'Weak MSSQL Creds',''),(11,2,14,'8080',''),(12,4,15,'Weak Tomcat Creds',''),(13,9,17,'%',''),(14,7,18,'%',''),(15,8,19,'%',''),(16,2,6,'8080',''),(17,2,6,'443',''),(18,2,6,'8443','');
/*!40000 ALTER TABLE `trigger_events` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vulnerabilities`
--

DROP TABLE IF EXISTS `vulnerabilities`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `vulnerabilities` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `port_data_id` int(11) NOT NULL,
  `vulnerability_descriptions_id` varchar(45) NOT NULL,
  `details` varchar(450) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `vulnerabilities`
--

LOCK TABLES `vulnerabilities` WRITE;
/*!40000 ALTER TABLE `vulnerabilities` DISABLE KEYS */;
/*!40000 ALTER TABLE `vulnerabilities` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vulnerability_descriptions`
--

DROP TABLE IF EXISTS `vulnerability_descriptions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `vulnerability_descriptions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `description` varchar(45) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `vulnerability_descriptions`
--

LOCK TABLES `vulnerability_descriptions` WRITE;
/*!40000 ALTER TABLE `vulnerability_descriptions` DISABLE KEYS */;
INSERT INTO `vulnerability_descriptions` VALUES (1,'MS08-067'),(2,'Weak MSSQL Creds'),(3,'Weak Tomcat Creds'),(4,'PsExec');
/*!40000 ALTER TABLE `vulnerability_descriptions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `websites`
--

DROP TABLE IF EXISTS `websites`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `websites` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `port_data_id` int(11) NOT NULL,
  `html_title` varchar(45) NOT NULL,
  `html_body` mediumtext NOT NULL,
  `screenshot` mediumblob,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `websites`
--

LOCK TABLES `websites` WRITE;
/*!40000 ALTER TABLE `websites` DISABLE KEYS */;
/*!40000 ALTER TABLE `websites` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping routines for database 'autodane'
--
/*!50003 DROP PROCEDURE IF EXISTS `addDomain` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = '' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `addDomain`(in _footprint_id int, in _domain_name varchar(45))
BEGIN
	if (select count(*) from domains where footprint_id = _footprint_id and domain_name = _domain_name) = 0 then
		insert into domains (footprint_id, domain_name) values (_footprint_id, _domain_name);
        
        call executeTriggers(_footprint_id, LAST_INSERT_ID(), 10, _domain_name);
    end if;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `addDomainCreds` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = '' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `addDomainCreds`(in _footprint_id int, in _host_data_id int, in _domain varchar(45), in _username varchar(45), in cleartext_password varchar(45))
BEGIN
    if (select count(*) from domain_credentials where footprint_id = _footprint_id and domain = _domain and username = _username) = 0 then
		insert into domain_credentials 
        (footprint_id, domain, username, cleartext_password) values
        (_footprint_id, _domain, _username, cleartext_password);
        
        call addToDomainCredentialsMap(_footprint_id, _host_data_id, LAST_INSERT_ID(), 1);
	end if;
    
    call addDomain(1, _domain);
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `addHost` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = '' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `addHost`(in _footprint_id int, in _ip_address varchar(45), in _host_name varchar(45), in _is_dc bit)
BEGIN
	DECLARE _net_range VARCHAR(45);
    set _net_range = (select concat(SUBSTRING(_ip_address, 1, length(_ip_address) - locate('.', reverse(_ip_address))), '.0/24'));
    
	if (select count(*) from host_data where footprint_id = _footprint_id and ip_address = _ip_address) = 0 then
		insert into host_data (footprint_id, ip_address, host_name) values (_footprint_id, _ip_address, _host_name);
        
        call executeTriggers(_footprint_id, LAST_INSERT_ID(), 1, _ip_address);
	end if;
    
    if (select count(*) from net_ranges where footprint_id = _footprint_id and net_range = _net_range) = 0 then
		insert into net_ranges (footprint_id, net_range) values (_footprint_id, _net_range);
        call executeTriggers(_footprint_id, LAST_INSERT_ID(), 3, _net_range);
    end if;
    
    if _host_name != "" then 
		update host_data set host_name = _host_name where footprint_id = _footprint_id and ip_address = _ip_address;
	end if;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `addLocalCredentials` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = '' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `addLocalCredentials`(in _host_data_id int(11), in _username varchar(45), in _cleartext_password varchar(100), in _lm_hash varchar(45), in _ntlm_hash varchar(45))
BEGIN
	if (select count(*) from local_credentials where host_data_id = _host_data_id and username = _username) = 0 then
		insert into local_credentials (host_data_id, username) values (_host_data_id, _username);
    end if;
    
    if (_cleartext_password != "") then
		update local_credentials set cleartext_password = _cleartext_password where host_data_id = _host_data_id and username = _username;
	end if;
    
    if (_lm_hash != "" and _ntlm_hash != "") then
		update local_credentials set lm_hash = _lm_hash, ntlm_hash = _ntlm_hash where host_data_id = _host_data_id and username = _username;
    end if;
    
    if (select count(*) from local_credentials lc join local_credentials_map m on lc.id = m.local_credentials_id where lc.host_data_id = _host_data_id and lc.username = _username) = 0 then
		insert into local_credentials_map (local_credentials_id, host_data_id, valid) select id, host_data_id, 1 from local_credentials where host_data_id = _host_data_id and username = _username;
    end if;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `addPort` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = '' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `addPort`(in _footprint_id int, in _host_data_id int, in _port_num int)
BEGIN
	if (select count(*) from port_data where host_data_id = _host_data_id and port_number = _port_num) = 0 then
		insert into port_data (host_data_id, port_number) values (_host_data_id, _port_num);
        call executeTriggers(_footprint_id, LAST_INSERT_ID(), 2, _port_num );
	end if;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `addScopeItem` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = '' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `addScopeItem`(in _footprint_id int, in _item_type int, in _item_value varchar(45))
BEGIN
	if (select count(*) from scope where footprint_id = _footprint_id and item_type = _item_type and item_value = _item_value) = 0 then
		insert into scope (footprint_id, item_type, item_value) values (_footprint_id, _item_type, _item_value);
        
        if _item_type = 1 then
			call executeTriggers(_footprint_id, LAST_INSERT_ID(), 6, _item_value); 
        end if;
        
        if _item_type = 2 then
			call executeTriggers(_footprint_id, LAST_INSERT_ID(), 7, _item_value); 
        end if;
    end if;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `addToDomainCredentialsMap` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = '' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `addToDomainCredentialsMap`(in _footprint_id int, in _host_data_id int, in _domain_credentials_id int, in _valid bit)
BEGIN
    if (select count(*) from domain_credentials_map where footprint_id = _footprint_id and host_data_id = _host_data_id and domain_credentials_id = _domain_credentials_id) = 0 then
		insert into domain_credentials_map
        (footprint_id, host_data_id, domain_credentials_id, valid) values
        (_footprint_id, _host_data_id, _domain_credentials_id, _valid);

        if (_valid) = 1 then
            #if (select count(*) from domain_credentials_map where domain_credentials_id in (select domain_credentials_id from domain_credentials_map where id = 1)) != 1 then
			call executeTriggers(_footprint_id, LAST_INSERT_ID(), 8, "");
            #end if;
		end if;
    end if;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `addToken` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = '' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `addToken`(in _host_id int, in _token varchar(100))
BEGIN
	if (select count(*) from tokens where host_id = _host_id and token = _token) = 0 then
		insert into tokens (host_id, token) values (_host_id, _token);
	end if;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `addToLocalCredentialsMap` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = '' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `addToLocalCredentialsMap`(in _host_data_id int, in _local_credentials_id int, in _valid bit)
BEGIN
	declare _username varchar(45);
	declare _cleartext_password varchar(45);
	declare _lm_hash varchar(45);
	declare _ntlm_hash varchar(45);
	declare credentials_id int;
    
	if (_valid) = 1 then
        select username, cleartext_password, lm_hash, ntlm_hash into _username, _cleartext_password, _lm_hash, _ntlm_hash  from local_credentials where id = _local_credentials_id;
        
		call addLocalCredentials(_host_data_id, _username, _cleartext_password, _lm_hash, _ntlm_hash);
        
        select id into credentials_id from local_credentials where (host_data_id, username, cleartext_password) in (select hd.id, lc.username, lc.cleartext_password from host_data hd, local_credentials lc where hd.id = _host_data_id and lc.id = _local_credentials_id);
        call executeTriggers((select footprint_id from host_data where id = _host_data_id), credentials_id, 5, "");
    else
		if (select count(*) from local_credentials_map where host_data_id = _host_data_id and local_credentials_id = _local_credentials_id) = 0 then
			insert into local_credentials_map (host_data_id, local_credentials_id, valid) values (_host_data_id, _local_credentials_id, _valid);
		end if;
	end if;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `addVulnerability` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = '' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `addVulnerability`(in _footprint_id int, in _port_data_id int, in _vulnerability_description_id int, in _details varchar(450))
BEGIN
    if (select count(*) from vulnerabilities where port_data_id = _port_data_id and vulnerability_descriptions_id = _vulnerability_description_id) = 0 then
		insert into vulnerabilities (port_data_id, vulnerability_descriptions_id, details) values (_port_data_id, _vulnerability_description_id, _details);
        
        call executeTriggers(_footprint_id, LAST_INSERT_ID(), 4, (select description from vulnerability_descriptions where id = _vulnerability_description_id));
    end if;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `addWebsite` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = '' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `addWebsite`(in _port_data_id int, in _html_title varchar(45), in _html_body MEDIUMTEXT, in _screenshot MEDIUMBLOB)
BEGIN
	if (select count(*) from websites where port_data_id = _port_data_id) = 0 then
		insert into websites (port_data_id, html_title, html_body, screenshot) values (_port_data_id, _html_title, _html_body, _screenshot);
	end if;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `createFootprint` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = '' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `createFootprint`(in _footprint_name varchar(45))
BEGIN
	if (select count(*) from footprints where footprint_name = _footprint_name) = 0 then
		insert into footprints (footprint_name) values (_footprint_name);
    end if;
	
	select id from footprints where footprint_name = _footprint_name;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `executeTriggers` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = '' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `executeTriggers`(in _footprint_id int, in _item_identifier int, in _trigger_event_id int, in _value varchar(450))
BEGIN
	insert into task_list (footprint_id, task_descriptions_id, item_identifier) 
	select 
		_footprint_id as 'footprint_id', td.id as 'task_descriptions_id', _item_identifier as 'item_identifier'
	from 
		task_categories tc
		join task_descriptions td on tc.id = td.task_categories_id
		join trigger_events te on te.task_descriptions_id = td.id
		join trigger_descriptions trd on trd.id = te.trigger_descriptions_id
	where 
		trd.id = _trigger_event_id and
		_value like te.value_mask and 
        te.enabled = 1;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `setDomainCredsVerified` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = '' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `setDomainCredsVerified`(in _footprint_id int, in _domain_credentials_map_id int)
BEGIN
	update
		domain_credentials dc
		join domain_credentials_map m on dc.id = m.domain_credentials_id
	set
		dc.verified = 1
	where
		m.id = _domain_credentials_map_id;
        
	call executeTriggers(_footprint_id, _domain_credentials_map_id, 9, "");
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `updateTaskStatus` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = '' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `updateTaskStatus`(in _task_id int, in _in_progress bit, in _completed bit, in _log MEDIUMTEXT)
BEGIN
	update task_list set in_progress = _in_progress, completed = _completed, log = _log where id = _task_id;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2015-12-03  2:04:37
