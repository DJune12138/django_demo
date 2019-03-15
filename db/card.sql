-- MySQL dump 10.13  Distrib 5.7.24, for macos10.14 (x86_64)
--
-- Host: 10.21.210.175    Database: yx_card
-- ------------------------------------------------------
-- Server version	5.6.20-log

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

DROP DATABASE IF EXISTS `yx_card`;

CREATE DATABASE `yx_card` DEFAULT CHARACTER SET utf8 COLLATE utf8_unicode_ci;

USE `yx_card`;

--
-- Table structure for table `admin_info`
--

DROP TABLE IF EXISTS `admin_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `admin_info` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `admin_id` int(11) NOT NULL,
  `email` varchar(75) NOT NULL,
  `qq` varchar(15) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `admin_info_ff7221fb` (`admin_id`),
  CONSTRAINT `admin_id_refs_id_697b6ff5` FOREIGN KEY (`admin_id`) REFERENCES `admins_new` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `admins_new`
--

DROP TABLE IF EXISTS `admins_new`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `admins_new` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `alias` varchar(50) NOT NULL,
  `username` varchar(50) NOT NULL,
  `password` varchar(32) NOT NULL,
  `last_ip` varchar(20) NOT NULL,
  `create_time` datetime NOT NULL,
  `last_time` datetime NOT NULL,
  `login_count` int(11) NOT NULL,
  `status` int(11) NOT NULL,
  `session_key` varchar(40) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  KEY `admins_new_5a09fd37` (`alias`),
  KEY `admins_new_c74d05a8` (`password`),
  KEY `admins_new_f33fecdb` (`session_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `admins_new_role`
--

DROP TABLE IF EXISTS `admins_new_role`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `admins_new_role` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `admin_id` int(11) NOT NULL,
  `role_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `admin_id` (`admin_id`,`role_id`),
  KEY `admins_new_role_ff7221fb` (`admin_id`),
  KEY `admins_new_role_278213e1` (`role_id`),
  CONSTRAINT `admin_id_refs_id_798479d2` FOREIGN KEY (`admin_id`) REFERENCES `admins_new` (`id`),
  CONSTRAINT `role_id_refs_id_2ec6d7b1` FOREIGN KEY (`role_id`) REFERENCES `role_new` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `agent`
--

DROP TABLE IF EXISTS `agent`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `agent` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(20) NOT NULL,
  `alias` varchar(20) NOT NULL,
  `username` varchar(20) NOT NULL,
  `password` varchar(50) NOT NULL,
  `create_time` datetime NOT NULL,
  `last_time` datetime NOT NULL,
  `last_ip` varchar(20) NOT NULL,
  `login_count` int(11) NOT NULL,
  `session_key` varchar(40) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `agent_4da47e07` (`name`),
  KEY `agent_ee0cafa2` (`username`),
  KEY `agent_c74d05a8` (`password`),
  KEY `agent_f33fecdb` (`session_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `agent_channel`
--

DROP TABLE IF EXISTS `agent_channel`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `agent_channel` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `agent_id` int(11) NOT NULL,
  `channel_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `agent_id` (`agent_id`,`channel_id`),
  KEY `agent_channel_44625c0c` (`agent_id`),
  KEY `agent_channel_9e85bf2d` (`channel_id`),
  CONSTRAINT `agent_id_refs_id_aeedb2b5` FOREIGN KEY (`agent_id`) REFERENCES `agent` (`id`),
  CONSTRAINT `channel_id_refs_id_b2d189a4` FOREIGN KEY (`channel_id`) REFERENCES `channel` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `agent_server`
--

DROP TABLE IF EXISTS `agent_server`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `agent_server` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `agent_id` int(11) NOT NULL,
  `server_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `agent_id` (`agent_id`,`server_id`),
  KEY `agent_server_44625c0c` (`agent_id`),
  KEY `agent_server_2f18fe12` (`server_id`),
  CONSTRAINT `agent_id_refs_id_54b49511` FOREIGN KEY (`agent_id`) REFERENCES `agent` (`id`),
  CONSTRAINT `server_id_refs_id_82e965c2` FOREIGN KEY (`server_id`) REFERENCES `servers` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `agent_server_group`
--

DROP TABLE IF EXISTS `agent_server_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `agent_server_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `agent_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `agent_id` (`agent_id`,`group_id`),
  KEY `agent_server_group_44625c0c` (`agent_id`),
  KEY `agent_server_group_5f412f9a` (`group_id`),
  CONSTRAINT `agent_id_refs_id_fc6a26a0` FOREIGN KEY (`agent_id`) REFERENCES `agent` (`id`),
  CONSTRAINT `group_id_refs_id_3e13a0a6` FOREIGN KEY (`group_id`) REFERENCES `groups` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `card_0`
--

DROP TABLE IF EXISTS `card_0`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `card_0` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `batch_id` int(11) NOT NULL,
  `number` varchar(32) NOT NULL,
  `password` varchar(32) DEFAULT NULL,
  `add_time` datetime NOT NULL,
  `use_time` datetime DEFAULT NULL,
  `server_id` int(11) DEFAULT NULL,
  `player_id` int(11) DEFAULT NULL,
  `channel_key` varchar(20) DEFAULT NULL,
  `status` int(11) DEFAULT NULL,
  `use_count` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `number` (`number`),
  KEY `card_0_12927864` (`batch_id`),
  KEY `card_0_eb822f1d` (`server_id`),
  KEY `card_0_5ef042d9` (`player_id`),
  CONSTRAINT `batch_id_refs_id_d3c1d463` FOREIGN KEY (`batch_id`) REFERENCES `card_batch` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `card_batch`
--

DROP TABLE IF EXISTS `card_batch`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `card_batch` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `server` varchar(1000) NOT NULL,
  `channels` varchar(1000) NOT NULL,
  `key` varchar(10) NOT NULL,
  `name` varchar(32) NOT NULL,
  `level` int(11) NOT NULL,
  `remark` varchar(255) NOT NULL,
  `total_count` int(11) NOT NULL,
  `used_count` int(11) NOT NULL,
  `limit_count` int(11) NOT NULL,
  `card_limit_count` int(11) NOT NULL,
  `prize` varchar(8192) NOT NULL,
  `start_time` datetime NOT NULL,
  `end_time` datetime NOT NULL,
  `code` varchar(32) NOT NULL,
  `show` int(11) NOT NULL,
  `status` int(11) NOT NULL,
  `other_condition` varchar(3000) NOT NULL,
  `create_user` int(10) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `card_log`
--

DROP TABLE IF EXISTS `card_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `card_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `server_id` int(11) DEFAULT NULL,
  `player_id` int(11) DEFAULT NULL,
  `number` varchar(32) NOT NULL,
  `channel_key` varchar(20) DEFAULT NULL,
  `card_key` varchar(10) NOT NULL,
  `card_name` varchar(30) NOT NULL,
  `prize` varchar(8192) NOT NULL,
  `create_time` datetime NOT NULL,
  `status` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `card_log_eb822f1d` (`server_id`),
  KEY `card_log_5ef042d9` (`player_id`),
  KEY `card_log_d4e7917a` (`number`),
  KEY `card_log_7952171b` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `card_prize`
--

DROP TABLE IF EXISTS `card_prize`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `card_prize` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(32) NOT NULL,
  `code` varchar(32) NOT NULL,
  `start_time` datetime NOT NULL,
  `end_time` datetime NOT NULL,
  `config` varchar(2000) NOT NULL,
  `remark` varchar(255) NOT NULL,
  `status` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `card_prize_4da47e07` (`name`),
  KEY `card_prize_09bb5fb3` (`code`),
  KEY `card_prize_66db471f` (`start_time`),
  KEY `card_prize_a3457057` (`end_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `channel`
--

DROP TABLE IF EXISTS `channel`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `channel` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `key` varchar(20) NOT NULL,
  `login_key` varchar(32) NOT NULL,
  `name` varchar(20) NOT NULL,
  `username` varchar(20) NOT NULL,
  `password` varchar(50) NOT NULL,
  `create_time` datetime NOT NULL,
  `last_time` datetime DEFAULT NULL,
  `last_ip` varchar(20) NOT NULL,
  `logins` int(11) NOT NULL,
  `agent_name` varchar(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `channel_4aa80db0` (`agent_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `channel_other`
--

DROP TABLE IF EXISTS `channel_other`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `channel_other` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `cid` int(11) NOT NULL,
  `data` longtext NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `cid` (`cid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `def_dict`
--

DROP TABLE IF EXISTS `def_dict`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `def_dict` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `key` varchar(50) NOT NULL,
  `_dict` longtext NOT NULL,
  `group` varchar(50) NOT NULL,
  `type` int(11) NOT NULL,
  `remark` varchar(400) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `key` (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `def_field`
--

DROP TABLE IF EXISTS `def_field`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `def_field` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `log_type` int(11) NOT NULL,
  `field_type` varchar(20) NOT NULL,
  `field_name` varchar(50) NOT NULL,
  `name` varchar(50) NOT NULL,
  `field_format` varchar(100) NOT NULL,
  `create_index` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `def_log`
--

DROP TABLE IF EXISTS `def_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `def_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `key` varchar(20) NOT NULL,
  `name` varchar(50) NOT NULL,
  `remark` varchar(1000) NOT NULL,
  `status` int(11) NOT NULL,
  `_config` longtext NOT NULL,
  `trigger` longtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `def_log_c0d4be93` (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `def_value`
--

DROP TABLE IF EXISTS `def_value`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `def_value` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `field_id` int(11) NOT NULL,
  `value_id` int(11) NOT NULL,
  `value` varchar(100) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_b7b81f0c` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `grouplist`
--

DROP TABLE IF EXISTS `grouplist`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `grouplist` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `key` varchar(20) NOT NULL,
  `name` varchar(50) NOT NULL,
  `order` int(11) NOT NULL,
  `partion_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `grouplist_36618f6a` (`partion_id`),
  CONSTRAINT `partion_id_refs_id_2896a1f5` FOREIGN KEY (`partion_id`) REFERENCES `groups` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `grouplist_server`
--

DROP TABLE IF EXISTS `grouplist_server`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `grouplist_server` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `grouplist_id` int(11) NOT NULL,
  `server_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `grouplist_id` (`grouplist_id`,`server_id`),
  KEY `grouplist_server_6fa08e58` (`grouplist_id`),
  KEY `grouplist_server_2f18fe12` (`server_id`),
  CONSTRAINT `grouplist_id_refs_id_65d315ea` FOREIGN KEY (`grouplist_id`) REFERENCES `grouplist` (`id`),
  CONSTRAINT `server_id_refs_id_ab389d55` FOREIGN KEY (`server_id`) REFERENCES `servers` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `groups`
--

DROP TABLE IF EXISTS `groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `groups` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `key` varchar(20) NOT NULL,
  `name` varchar(50) NOT NULL,
  `custom_url` varchar(100) NOT NULL,
  `pay_url` varchar(100) NOT NULL,
  `notice_url` varchar(100) NOT NULL,
  `upgrade_url` varchar(100) NOT NULL,
  `notice_select` int(11) NOT NULL,
  `remark` varchar(200) NOT NULL,
  `other` varchar(500) NOT NULL,
  `pid_list` varchar(500) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `groups_server`
--

DROP TABLE IF EXISTS `groups_server`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `groups_server` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) NOT NULL,
  `server_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `group_id` (`group_id`,`server_id`),
  KEY `groups_server_5f412f9a` (`group_id`),
  KEY `groups_server_2f18fe12` (`server_id`),
  CONSTRAINT `group_id_refs_id_a45294a9` FOREIGN KEY (`group_id`) REFERENCES `groups` (`id`),
  CONSTRAINT `server_id_refs_id_6f0d3920` FOREIGN KEY (`server_id`) REFERENCES `servers` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `kuafu_servers`
--

DROP TABLE IF EXISTS `kuafu_servers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `kuafu_servers` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `client_ver` varchar(500) NOT NULL,
  `name` varchar(20) NOT NULL,
  `alias` varchar(20) NOT NULL,
  `game_addr` varchar(100) NOT NULL,
  `game_port` int(11) NOT NULL,
  `log_db_config` varchar(500) NOT NULL,
  `report_url` varchar(100) NOT NULL,
  `status` int(11) NOT NULL,
  `create_time` datetime NOT NULL,
  `require_ver` int(11) NOT NULL,
  `remark` varchar(200) NOT NULL,
  `json_data` varchar(1000) NOT NULL,
  `order` int(11) NOT NULL,
  `commend` int(11) NOT NULL,
  `is_ios` int(11) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `log_0_new`
--

DROP TABLE IF EXISTS `log_0_new`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `log_0_new` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `log_time` datetime NOT NULL,
  `log_type` int(11) NOT NULL,
  `log_tag` int(11) DEFAULT NULL,
  `log_user` int(11) DEFAULT NULL,
  `log_name` varchar(100) DEFAULT NULL,
  `log_server` int(11) DEFAULT NULL,
  `log_level` int(11) DEFAULT NULL,
  `log_previous` varchar(200) DEFAULT NULL,
  `log_now` varchar(200) DEFAULT NULL,
  `log_relate` varchar(32) DEFAULT NULL,
  `f1` varchar(100) DEFAULT NULL,
  `f2` varchar(100) DEFAULT NULL,
  `f3` varchar(100) DEFAULT NULL,
  `f4` varchar(100) DEFAULT NULL,
  `f5` varchar(100) DEFAULT NULL,
  `f6` longtext,
  `f7` varchar(100) DEFAULT NULL,
  `f8` longtext,
  `log_channel` int(11) DEFAULT NULL,
  `log_data` int(11) DEFAULT NULL,
  `log_result` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `log_0_new_e66fcc8f` (`log_time`),
  KEY `log_0_new_4e1535f2` (`log_user`),
  KEY `log_0_new_7ad0ef9c` (`log_relate`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `menu_new`
--

DROP TABLE IF EXISTS `menu_new`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `menu_new` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `parent_id` int(11) NOT NULL,
  `name` varchar(50) NOT NULL,
  `url` varchar(400) NOT NULL,
  `url_path` varchar(100) NOT NULL,
  `icon` varchar(100) DEFAULT NULL,
  `css` varchar(100) DEFAULT NULL,
  `order` int(11) NOT NULL,
  `is_show` int(11) NOT NULL,
  `is_log` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `menu_new_ecb85c87` (`url_path`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `player_0`
--

DROP TABLE IF EXISTS `player_0`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `player_0` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `player_id` int(11) NOT NULL,
  `player_name` varchar(50) NOT NULL,
  `user_type` int(11) NOT NULL,
  `link_key` varchar(50) NOT NULL,
  `create_time` datetime NOT NULL,
  `last_time` datetime NOT NULL,
  `last_ip` varchar(32) NOT NULL,
  `last_key` varchar(50) DEFAULT NULL,
  `login_num` int(11) NOT NULL,
  `status` int(11) NOT NULL,
  `channel_id` varchar(20) NOT NULL,
  `mobile_key` varchar(50) DEFAULT NULL,
  `other` varchar(500) DEFAULT NULL,
  `is_old` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `player_id` (`player_id`),
  KEY `player_0_e3de4779` (`player_name`),
  KEY `player_0_f96a0352` (`user_type`),
  KEY `player_0_acd89b05` (`link_key`),
  KEY `player_0_7952171b` (`create_time`),
  KEY `player_0_6aae6f5d` (`last_time`),
  KEY `player_0_0702f4f0` (`last_key`),
  KEY `player_0_69a8080e` (`channel_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `resource`
--

DROP TABLE IF EXISTS `resource`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `resource` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(20) NOT NULL,
  `role_id` int(11) NOT NULL,
  `_members` longtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `resource_4da47e07` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `role_new`
--

DROP TABLE IF EXISTS `role_new`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `role_new` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `parent_name` varchar(50) NOT NULL,
  `type` int(11) NOT NULL,
  `remark` varchar(1000) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `role_new_b588ddd1` (`parent_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `role_new_resource`
--

DROP TABLE IF EXISTS `role_new_resource`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `role_new_resource` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `role_id` int(11) NOT NULL,
  `resource_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `role_id` (`role_id`,`resource_id`),
  KEY `role_new_resource_278213e1` (`role_id`),
  KEY `role_new_resource_217f3d22` (`resource_id`),
  CONSTRAINT `resource_id_refs_id_4b9605eb` FOREIGN KEY (`resource_id`) REFERENCES `resource` (`id`),
  CONSTRAINT `role_id_refs_id_6bbaaa91` FOREIGN KEY (`role_id`) REFERENCES `role_new` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `servers`
--

DROP TABLE IF EXISTS `servers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `servers` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `client_ver` varchar(500) NOT NULL,
  `name` varchar(20) NOT NULL,
  `alias` varchar(20) NOT NULL,
  `game_addr` varchar(100) NOT NULL,
  `game_port` int(11) NOT NULL,
  `log_db_config` varchar(500) NOT NULL,
  `report_url` varchar(100) NOT NULL,
  `status` int(11) NOT NULL,
  `create_time` datetime NOT NULL,
  `require_ver` int(11) NOT NULL,
  `remark` varchar(200) NOT NULL,
  `json_data` varchar(1000) NOT NULL,
  `order` int(11) NOT NULL,
  `commend` int(11) NOT NULL,
  `is_ios` int(11) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `work_log`
--

DROP TABLE IF EXISTS `work_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `work_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `work_number` varchar(50) NOT NULL,
  `add_time` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `work_number` (`work_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2019-01-31 11:51:46

commit;