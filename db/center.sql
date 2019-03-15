-- MySQL dump 10.13  Distrib 5.7.24, for macos10.14 (x86_64)
--
-- Host: 10.21.210.175    Database: yx_center
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

DROP DATABASE IF EXISTS `yx_center`;

CREATE DATABASE `yx_center` DEFAULT CHARACTER SET utf8 COLLATE utf8_unicode_ci;

USE `yx_center`;

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
  `last_ip` varchar(128) NOT NULL,
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
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
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
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
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
  `last_ip` varchar(128) NOT NULL,
  `login_count` int(11) NOT NULL,
  `session_key` varchar(40) NOT NULL,
  `game_app_key` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `agent_4da47e07` (`name`),
  KEY `agent_ee0cafa2` (`username`),
  KEY `agent_c74d05a8` (`password`),
  KEY `agent_f33fecdb` (`session_key`),
  KEY `gameAppKey` (`game_app_key`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8;
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
  UNIQUE KEY `agent_id` (`agent_id`,`group_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth`
--

DROP TABLE IF EXISTS `auth`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `auth_type` int(11) NOT NULL,
  `user_type` int(11) NOT NULL,
  `link_key` varchar(50) NOT NULL,
  `access_token` varchar(100) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `banip_list`
--

DROP TABLE IF EXISTS `banip_list`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `banip_list` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(128) NOT NULL,
  `ip` varchar(32) NOT NULL,
  `last_time` datetime NOT NULL,
  `status` int(11) NOT NULL,
  `other` varchar(500) DEFAULT NULL,
  `f1` int(11) DEFAULT NULL,
  `f2` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ip` (`ip`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `battle_list`
--

DROP TABLE IF EXISTS `battle_list`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `battle_list` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `server` int(11) NOT NULL,
  `create_time` datetime NOT NULL,
  `last_time` datetime DEFAULT NULL,
  `sort` int(11) DEFAULT NULL,
  `group` varchar(10) DEFAULT NULL,
  `sub_group` varchar(10) DEFAULT NULL,
  `sub_server` varchar(100) DEFAULT NULL,
  `version` int(11) DEFAULT NULL,
  `f1` varchar(100) DEFAULT NULL,
  `f2` varchar(100) DEFAULT NULL,
  `f3` varchar(100) DEFAULT NULL,
  `f4` varchar(100) DEFAULT NULL,
  `f5` varchar(100) DEFAULT NULL,
  `f6` longtext,
  `f7` varchar(100) DEFAULT NULL,
  `f8` longtext,
  `status` int(10) DEFAULT NULL,
  `run_time` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `battle_list_2f18fe12` (`server`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `block_user`
--

DROP TABLE IF EXISTS `block_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `block_user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `server_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `block_user_6340c63c` (`user_id`),
  KEY `block_user_2f18fe12` (`server_id`),
  CONSTRAINT `server_id_refs_id_bfae41e8` FOREIGN KEY (`server_id`) REFERENCES `servers` (`id`),
  CONSTRAINT `user_id_refs_id_d341a3f8` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `calendar_events`
--

DROP TABLE IF EXISTS `calendar_events`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `calendar_events` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `creator` varchar(32) NOT NULL,
  `editor` varchar(32) NOT NULL,
  `event` varchar(100) NOT NULL,
  `descript` varchar(500) NOT NULL,
  `class_name` varchar(32) DEFAULT NULL,
  `all_day` int(11) NOT NULL,
  `start` datetime NOT NULL,
  `end` datetime NOT NULL,
  `update_time` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `channel`
--

DROP TABLE IF EXISTS `channel`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `channel` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `channel_key` varchar(50) DEFAULT NULL,
  `login_key` varchar(50) NOT NULL,
  `name` varchar(20) NOT NULL,
  `username` varchar(20) NOT NULL,
  `password` varchar(50) NOT NULL,
  `create_time` datetime NOT NULL,
  `last_time` datetime DEFAULT NULL,
  `last_ip` varchar(128) NOT NULL,
  `logins` int(11) NOT NULL,
  `group_name` varchar(20) NOT NULL,
  `game_app_key` varchar(50) DEFAULT NULL,
  `group_key` varchar(50) DEFAULT NULL,
  `allow_earn` int(11) DEFAULT NULL,
  `novice_mail` longtext DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `channel_4aa80db0` (`group_name`),
  KEY `gameAppKey` (`game_app_key`),
  KEY `gameAppKey_2` (`game_app_key`)
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8;
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
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `custom_menu`
--

DROP TABLE IF EXISTS `custom_menu`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `custom_menu` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `admin_id` int(11) NOT NULL,
  `defined_menu` longtext NOT NULL,
  `map_menu` longtext NOT NULL,
  `update_time` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
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
) ENGINE=InnoDB AUTO_INCREMENT=156 DEFAULT CHARSET=utf8;
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
-- Table structure for table `def_gm`
--

DROP TABLE IF EXISTS `def_gm`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `def_gm` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(50) NOT NULL,
  `description` varchar(200) NOT NULL,
  `url` varchar(50) NOT NULL,
  `params` varchar(6000) NOT NULL,
  `result_type` varchar(20) NOT NULL,
  `result_define` varchar(6000) NOT NULL,
  `flag` varchar(100) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1104 DEFAULT CHARSET=utf8;
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
  UNIQUE KEY `key` (`key`)
) ENGINE=InnoDB AUTO_INCREMENT=202 DEFAULT CHARSET=utf8;
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
-- Table structure for table `dict_value`
--

DROP TABLE IF EXISTS `dict_value`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `dict_value` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `dict_id` int(11) NOT NULL,
  `dict_name` varchar(75) DEFAULT NULL,
  `dict_price` longtext,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
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
-- Table structure for table `game_activity`
--

DROP TABLE IF EXISTS `game_activity`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `game_activity` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `info` varchar(1000) NOT NULL,
  `type` varchar(20) NOT NULL,
  `sdate` datetime NOT NULL,
  `edate` datetime NOT NULL,
  `msg` longtext NOT NULL,
  `is_auto` int(11) NOT NULL,
  `is_auto_off` int(11) NOT NULL,
  `is_temp` int(11) NOT NULL,
  `status` int(10) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `game_activity_4da47e07` (`name`),
  KEY `game_activity_403d8ff3` (`type`)
) ENGINE=InnoDB AUTO_INCREMENT=52 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `game_activity_server`
--

DROP TABLE IF EXISTS `game_activity_server`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `game_activity_server` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `activity_id` int(11) NOT NULL,
  `server_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `activity_id` (`activity_id`,`server_id`),
  KEY `game_activity_server_8005e431` (`activity_id`),
  KEY `game_activity_server_2f18fe12` (`server_id`),
  CONSTRAINT `activity_id_refs_id_3acad7d5` FOREIGN KEY (`activity_id`) REFERENCES `game_activity` (`id`),
  CONSTRAINT `server_id_refs_id_8474c004` FOREIGN KEY (`server_id`) REFERENCES `servers` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `game_activity_template`
--

DROP TABLE IF EXISTS `game_activity_template`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `game_activity_template` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `type` varchar(20) NOT NULL,
  `msg` longtext,
  `create_time` datetime NOT NULL,
  `create_user_name` varchar(20) NOT NULL,
  `info` varchar(1000) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `game_activity_template_403d8ff3` (`type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `game_platform`
--

DROP TABLE IF EXISTS `game_platform`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `game_platform` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `client_ver` varchar(500) NOT NULL,
  `name` varchar(20) NOT NULL,
  `key` varchar(20) NOT NULL,
  `app_key` varchar(50) NOT NULL,
  `address` varchar(200) NOT NULL,
  `channel_address` varchar(200) NOT NULL,
  `server_address` varchar(200) NOT NULL,
  `remark` varchar(500) NOT NULL,
  `time_zone` int(11) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `gang_0`
--

DROP TABLE IF EXISTS `gang_0`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `gang_0` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `gang_id` int(11) NOT NULL,
  `gang_name` varchar(50) NOT NULL,
  `create_time` datetime NOT NULL,
  `status` int(11) NOT NULL,
  `level` int(11) NOT NULL,
  `gang_master` int(11) NOT NULL,
  `build_level` varchar(500) NOT NULL,
  `gang_assets` int(11) NOT NULL,
  `declaration` varchar(500) NOT NULL,
  `gang_members` int(11) NOT NULL,
  `other` varchar(500) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `gang_id` (`gang_id`),
  KEY `gang_0_5608295d` (`gang_name`),
  KEY `gang_0_7952171b` (`create_time`)
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
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8;
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
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `groups`
--

DROP TABLE IF EXISTS `groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `groups` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `group_key` varchar(50) DEFAULT NULL,
  `name` varchar(50) NOT NULL,
  `login_url` varchar(100) DEFAULT NULL,
  `card_url` varchar(100) DEFAULT NULL,
  `notice_url` varchar(100) NOT NULL,
  `cdn_url` varchar(100) DEFAULT NULL,
  `notice_select` int(11) NOT NULL,
  `remark` varchar(200) NOT NULL,
  `other` varchar(10000) DEFAULT NULL,
  `pid_list` varchar(500) NOT NULL,
  `version` int(40) DEFAULT NULL,
  `custom_url` varchar(100) DEFAULT NULL,
  `sdk_url` varchar(100) DEFAULT NULL,
  `audit_version` int(40) DEFAULT NULL,
  `audit_server` int(40) DEFAULT NULL,
  `last_time` datetime DEFAULT NULL,
  `resource_version` int(40) DEFAULT NULL,
  `audit_servers` varchar(100) DEFAULT NULL,
  `audit_versions` varchar(100) DEFAULT NULL,
  `game_app_key` varchar(50) DEFAULT NULL,
  `novice_mail` longtext DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `groups_channel`
--

DROP TABLE IF EXISTS `groups_channel`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `groups_channel` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) NOT NULL,
  `channel_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `group_id` (`group_id`,`channel_id`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8;
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
) ENGINE=InnoDB AUTO_INCREMENT=174 DEFAULT CHARSET=utf8;
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
-- Table structure for table `log_add`
--

DROP TABLE IF EXISTS `log_add`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `log_add` (
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
  KEY `log_0_new_7ad0ef9c` (`log_relate`),
  KEY `log_add_log_user_index` (`log_user`),
  KEY `log_add_log_time_index` (`log_time`),
  KEY `log_add_log_relate_index` (`log_relate`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `log_all_online`
--

DROP TABLE IF EXISTS `log_all_online`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `log_all_online` (
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
-- Table structure for table `log_backstage`
--

DROP TABLE IF EXISTS `log_backstage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `log_backstage` (
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
  KEY `log_0_new_7ad0ef9c` (`log_relate`),
  KEY `log_backstage_log_user_index` (`log_user`),
  KEY `log_backstage_log_time_index` (`log_time`),
  KEY `log_backstage_log_relate_index` (`log_relate`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `log_get_platform_result`
--

DROP TABLE IF EXISTS `log_get_platform_result`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `log_get_platform_result` (
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
-- Table structure for table `log_gm`
--

DROP TABLE IF EXISTS `log_gm`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `log_gm` (
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
  KEY `log_0_new_7ad0ef9c` (`log_relate`),
  KEY `log_gm_log_user_index` (`log_user`),
  KEY `log_gm_log_time_index` (`log_time`),
  KEY `log_gm_log_relate_index` (`log_relate`)
) ENGINE=InnoDB AUTO_INCREMENT=106 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `log_kuafu`
--

DROP TABLE IF EXISTS `log_kuafu`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `log_kuafu` (
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
  KEY `log_0_new_7ad0ef9c` (`log_relate`),
  KEY `log_kuafu_log_user_index` (`log_user`),
  KEY `log_kuafu_log_time_index` (`log_time`),
  KEY `log_kuafu_log_relate_index` (`log_relate`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `log_mail`
--

DROP TABLE IF EXISTS `log_mail`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `log_mail` (
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
  KEY `log_0_new_7ad0ef9c` (`log_relate`),
  KEY `log_mail_log_user_index` (`log_user`),
  KEY `log_mail_log_time_index` (`log_time`),
  KEY `log_mail_log_relate_index` (`log_relate`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `log_neibuhao`
--

DROP TABLE IF EXISTS `log_neibuhao`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `log_neibuhao` (
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
  `log_relate` varchar(100) DEFAULT NULL,
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
  KEY `log_0_new_7ad0ef9c` (`log_relate`),
  KEY `log_neibuhao_log_user_index` (`log_user`),
  KEY `log_neibuhao_log_time_index` (`log_time`),
  KEY `log_neibuhao_log_relate_index` (`log_relate`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `log_open`
--

DROP TABLE IF EXISTS `log_open`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `log_open` (
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
  KEY `log_0_new_7ad0ef9c` (`log_relate`),
  KEY `log_open_log_time_index` (`log_time`),
  KEY `log_open_f5_index` (`f5`),
  KEY `log_open_f4_index` (`f4`),
  KEY `log_open_f3_index` (`f3`),
  KEY `log_open_f2_index` (`f2`),
  KEY `log_open_f1_index` (`f1`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `log_operate`
--

DROP TABLE IF EXISTS `log_operate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `log_operate` (
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
  `f7` datetime DEFAULT NULL,
  `f8` int(11) DEFAULT NULL,
  `log_channel` int(11) DEFAULT NULL,
  `log_data` int(11) DEFAULT NULL,
  `log_result` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `log_0_new_e66fcc8f` (`log_time`),
  KEY `log_0_new_4e1535f2` (`log_user`),
  KEY `log_0_new_7ad0ef9c` (`log_relate`),
  KEY `log_operate_log_user_index` (`log_user`),
  KEY `log_operate_log_time_index` (`log_time`),
  KEY `log_operate_log_channel_index` (`log_channel`),
  KEY `log_operate_f3_index` (`f3`),
  KEY `log_operate_f2_index` (`f2`)
) ENGINE=InnoDB AUTO_INCREMENT=141 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `log_pay`
--

DROP TABLE IF EXISTS `log_pay`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `log_pay` (
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
  KEY `log_0_new_7ad0ef9c` (`log_relate`),
  KEY `log_pay_log_user_index` (`log_user`),
  KEY `log_pay_log_time_index` (`log_time`),
  KEY `log_pay_log_relate_index` (`log_relate`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `log_platform_result`
--

DROP TABLE IF EXISTS `log_platform_result`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `log_platform_result` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `log_type` int(11) NOT NULL,
  `log_user` int(11) DEFAULT NULL,
  `log_name` varchar(100) DEFAULT NULL,
  `log_server` int(11) DEFAULT NULL,
  `log_channel` int(11) DEFAULT NULL,
  `log_data` int(11) DEFAULT NULL,
  `log_result` int(11) DEFAULT NULL,
  `log_level` int(11) DEFAULT NULL,
  `log_time` datetime NOT NULL,
  `log_previous` varchar(200) DEFAULT NULL,
  `log_now` varchar(200) DEFAULT NULL,
  `log_tag` int(11) DEFAULT NULL,
  `f1` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`,`log_time`),
  KEY `log_platform_result_log_type` (`log_type`),
  KEY `log_platform_result_log_time` (`log_time`),
  KEY `log_platform_result_log_server` (`log_server`),
  KEY `log_platform_result_log_channel` (`log_channel`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8
/*!50100 PARTITION BY RANGE (year(log_time))
(PARTITION p201x VALUES LESS THAN (2010) ENGINE = InnoDB,
 PARTITION p2010 VALUES LESS THAN (2011) ENGINE = InnoDB,
 PARTITION p2011 VALUES LESS THAN (2012) ENGINE = InnoDB,
 PARTITION p2012 VALUES LESS THAN (2013) ENGINE = InnoDB,
 PARTITION p2013 VALUES LESS THAN (2014) ENGINE = InnoDB,
 PARTITION p2014 VALUES LESS THAN (2015) ENGINE = InnoDB,
 PARTITION p2015 VALUES LESS THAN (2016) ENGINE = InnoDB,
 PARTITION p2016 VALUES LESS THAN (2017) ENGINE = InnoDB,
 PARTITION p2017 VALUES LESS THAN (2018) ENGINE = InnoDB,
 PARTITION p2018 VALUES LESS THAN (2019) ENGINE = InnoDB,
 PARTITION p2019 VALUES LESS THAN (2020) ENGINE = InnoDB,
 PARTITION p202x VALUES LESS THAN MAXVALUE ENGINE = InnoDB) */;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `log_platform_result_tmp`
--

DROP TABLE IF EXISTS `log_platform_result_tmp`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `log_platform_result_tmp` (
  `log_type` int(11) NOT NULL,
  `log_user` int(11) DEFAULT NULL,
  `log_name` varchar(100) DEFAULT NULL,
  `log_server` int(11) DEFAULT NULL,
  `log_channel` int(11) DEFAULT NULL,
  `log_data` int(11) DEFAULT NULL,
  `log_result` int(11) DEFAULT NULL,
  `log_level` int(11) DEFAULT NULL,
  `log_time` datetime NOT NULL,
  `log_previous` varchar(200) DEFAULT NULL,
  `log_now` varchar(200) DEFAULT NULL,
  `log_tag` int(11) DEFAULT NULL,
  `f1` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `log_player_history`
--

DROP TABLE IF EXISTS `log_player_history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `log_player_history` (
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
  KEY `log_0_new_7ad0ef9c` (`log_relate`),
  KEY `log_player_history_log_user_index` (`log_user`),
  KEY `log_player_history_log_time_index` (`log_time`),
  KEY `log_player_history_log_tag_index` (`log_tag`),
  KEY `log_player_history_log_server_index` (`log_server`),
  KEY `log_player_history_log_relate_index` (`log_relate`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `log_statistic_date`
--

DROP TABLE IF EXISTS `log_statistic_date`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `log_statistic_date` (
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
  KEY `log_0_new_7ad0ef9c` (`log_relate`),
  KEY `log_statistic_date_log_time_index` (`log_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `log_statistic_result`
--

DROP TABLE IF EXISTS `log_statistic_result`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `log_statistic_result` (
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
  `log_channel` varchar(20) DEFAULT NULL,
  `log_data` int(11) DEFAULT NULL,
  `log_result` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `log_0_new_e66fcc8f` (`log_type`),
  KEY `log_0_new_4e1535f2` (`log_user`),
  KEY `log_0_new_7ad0ef9c` (`log_relate`),
  KEY `log_statistic_result_log_user_index` (`log_user`),
  KEY `log_statistic_result_log_time_index` (`log_time`),
  KEY `log_statistic_result_log_relate_index` (`log_relate`)
) ENGINE=InnoDB AUTO_INCREMENT=829 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `log_system_page`
--

DROP TABLE IF EXISTS `log_system_page`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `log_system_page` (
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
  KEY `log_0_new_7ad0ef9c` (`log_relate`),
  KEY `log_system_page_log_user_index` (`log_user`),
  KEY `log_system_page_log_time_index` (`log_time`),
  KEY `log_system_page_log_relate_index` (`log_relate`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `mail_list`
--

DROP TABLE IF EXISTS `mail_list`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `mail_list` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(50) NOT NULL,
  `content` varchar(1000) NOT NULL,
  `bonus_content` varchar(1000) NOT NULL,
  `status` int(11) NOT NULL,
  `type` int(11) NOT NULL,
  `create_time` datetime NOT NULL,
  `server_ids` varchar(1000) DEFAULT NULL,
  `channel_id` int(11) DEFAULT NULL,
  `player_id` varchar(1000) DEFAULT NULL,
  `Applicant` varchar(50) NOT NULL,
  `Auditor` varchar(50) DEFAULT NULL,
  `time_status` int(11) DEFAULT '0',
  `order_time` datetime DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  KEY `mail_list_9246ed76` (`title`) USING BTREE,
  KEY `mail_list_48fb58bb` (`status`) USING BTREE,
  KEY `mail_list_5ef042d9` (`player_id`(255)) USING BTREE,
  KEY `mail_list_592b81a0` (`Applicant`) USING BTREE,
  KEY `mail_list_831ed528` (`Auditor`) USING BTREE,
  KEY `mail_list_timestat` (`time_status`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=608 DEFAULT CHARSET=utf8 ROW_FORMAT=COMPACT;
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
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `name` (`name`) USING BTREE,
  KEY `menu_new_ecb85c87` (`url_path`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=602 DEFAULT CHARSET=utf8 ROW_FORMAT=COMPACT;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `notice`
--

DROP TABLE IF EXISTS `notice`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `notice` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `client_ver` varchar(50) NOT NULL,
  `title` varchar(200) NOT NULL,
  `content` longtext NOT NULL,
  `link_url` varchar(100) NOT NULL,
  `begin_time` datetime NOT NULL,
  `end_time` datetime NOT NULL,
  `status` int(11) NOT NULL,
  `pub_ip` varchar(20) NOT NULL,
  `pub_user` int(11) NOT NULL,
  `notice_type` int(11) NOT NULL,
  `intervalSecond` int(11) NOT NULL,
  `size` varchar(20) NOT NULL,
  `tag` int(11) DEFAULT NULL,
  `is_temp` int(11) NOT NULL,
  `create_time` bigint(20) NOT NULL,
  `sort` int(11) DEFAULT NULL,
  `sub_title` varchar(200) DEFAULT NULL,
  `photo_id` int(10) DEFAULT NULL,
  `jump` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `notice_0364c35d` (`begin_time`),
  KEY `notice_a3457057` (`end_time`),
  KEY `notice_278b5eba` (`pub_user`)
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `notice_channel`
--

DROP TABLE IF EXISTS `notice_channel`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `notice_channel` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `notice_id` int(11) NOT NULL,
  `channel_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `notice_id` (`notice_id`,`channel_id`),
  KEY `notice_channel_9166e810` (`notice_id`),
  KEY `notice_channel_9e85bf2d` (`channel_id`),
  CONSTRAINT `channel_id_refs_id_f5e6959f` FOREIGN KEY (`channel_id`) REFERENCES `channel` (`id`),
  CONSTRAINT `notice_id_refs_id_5bd086ac` FOREIGN KEY (`notice_id`) REFERENCES `notice` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `notice_group`
--

DROP TABLE IF EXISTS `notice_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `notice_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `notice_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `notice_id` (`notice_id`,`group_id`),
  KEY `notice_group_9166e810` (`notice_id`),
  KEY `notice_group_5f412f9a` (`group_id`),
  CONSTRAINT `group_id_refs_id_d409fc75` FOREIGN KEY (`group_id`) REFERENCES `groups` (`id`),
  CONSTRAINT `notice_id_refs_id_ac6286c8` FOREIGN KEY (`notice_id`) REFERENCES `notice` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `notice_server`
--

DROP TABLE IF EXISTS `notice_server`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `notice_server` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `notice_id` int(11) NOT NULL,
  `server_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `notice_id` (`notice_id`,`server_id`),
  KEY `notice_server_9166e810` (`notice_id`),
  KEY `notice_server_2f18fe12` (`server_id`),
  CONSTRAINT `notice_id_refs_id_1afc415d` FOREIGN KEY (`notice_id`) REFERENCES `notice` (`id`),
  CONSTRAINT `server_id_refs_id_a5b9d895` FOREIGN KEY (`server_id`) REFERENCES `servers` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=99 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `pay_action`
--

DROP TABLE IF EXISTS `pay_action`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `pay_action` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `query_id` varchar(40) NOT NULL,
  `order_id` varchar(60) DEFAULT NULL,
  `channel_key` varchar(50) DEFAULT NULL,
  `channel_id` int(11) NOT NULL,
  `server_id` int(11) NOT NULL,
  `pay_type` int(11) NOT NULL,
  `pay_user` int(11) NOT NULL,
  `pay_ip` varchar(20) NOT NULL,
  `pay_status` int(11) NOT NULL,
  `card_no` varchar(50) NOT NULL,
  `card_pwd` varchar(50) NOT NULL,
  `post_time` datetime NOT NULL,
  `last_time` datetime DEFAULT NULL,
  `post_amount` double NOT NULL,
  `pay_amount` double NOT NULL,
  `pay_gold` int(11) NOT NULL,
  `extra` double NOT NULL,
  `remark` varchar(200) DEFAULT NULL,
  `open_id` varchar(100) DEFAULT NULL,
  `count` int(11) NOT NULL,
  `player_name` varchar(50) NOT NULL,
  `player_create_time` datetime DEFAULT NULL,
  `charge_type` int(20) DEFAULT NULL,
  `charge_id` int(20) DEFAULT NULL,
  `payType` varchar(100) DEFAULT NULL,
  `channel_sub_key` varchar(50) DEFAULT NULL,
  `vip_level` int(10) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `pay_action_55fcdee3` (`query_id`),
  KEY `pay_action_1b89fe59` (`order_id`),
  KEY `pay_action_69a8080e` (`channel_id`),
  KEY `pay_action_eb822f1d` (`server_id`),
  KEY `pay_action_2d8569e3` (`pay_type`),
  KEY `pay_action_5361dc42` (`pay_user`),
  KEY `pay_action_75f6668a` (`pay_status`),
  KEY `pay_action_6aae6f5d` (`last_time`),
  KEY `pay_action_1d850ceb` (`open_id`),
  KEY `pay_action_035145bf` (`player_create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `pay_channel`
--

DROP TABLE IF EXISTS `pay_channel`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `pay_channel` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `server_id` int(11) NOT NULL,
  `channel_key` varchar(200) NOT NULL,
  `name` varchar(100) NOT NULL,
  `link_id` varchar(50) NOT NULL,
  `icon` varchar(20) NOT NULL,
  `func_name` varchar(20) NOT NULL,
  `pay_type` int(11) NOT NULL,
  `post_url` varchar(500) NOT NULL,
  `notice_url` varchar(500) NOT NULL,
  `pay_config` varchar(1000) NOT NULL,
  `remark` varchar(200) NOT NULL,
  `exchange_rate` double NOT NULL,
  `status` int(11) NOT NULL,
  `order` int(11) NOT NULL,
  `unit` varchar(10) NOT NULL,
  `currency` varchar(10) NOT NULL,
  `amount` double NOT NULL,
  `card_key` varchar(200) NOT NULL,
  `gold` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `pay_channel_eb822f1d` (`server_id`),
  KEY `pay_channel_a050c82a` (`link_id`)
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
  `last_ip` varchar(128) NOT NULL,
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
-- Table structure for table `player_all`
--

DROP TABLE IF EXISTS `player_all`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `player_all` (
  `server_id` int(11) NOT NULL,
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
  `roll_num` int(11) DEFAULT '0',
  UNIQUE KEY `player_id` (`player_id`),
  KEY `user_type_link_key_index` (`link_key`,`user_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `player_operation`
--

DROP TABLE IF EXISTS `player_operation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `player_operation` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `player_id` int(11) NOT NULL,
  `type` varchar(200) NOT NULL,
  `scene_id` varchar(100) NOT NULL,
  `account` varchar(200) NOT NULL,
  `content` varchar(1000) NOT NULL,
  `create_time` datetime NOT NULL,
  `app_name` varchar(200) NOT NULL,
  `bundle_id` varchar(200) NOT NULL,
  `device_id` varchar(200) NOT NULL,
  `channel_key` varchar(200) NOT NULL,
  `extra` varchar(500) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `player_operation_5ef042d9` (`player_id`),
  KEY `player_operation_403d8ff3` (`type`),
  KEY `player_operation_ccedb0af` (`scene_id`),
  KEY `player_operation_93025c2f` (`account`),
  KEY `player_operation_7952171b` (`create_time`),
  KEY `player_operation_fc8c2439` (`bundle_id`),
  KEY `player_operation_6d993ecb` (`device_id`),
  KEY `player_operation_9b5dc9b1` (`channel_key`),
  KEY `player_operation_92617ad4` (`extra`(255))
) ENGINE=InnoDB AUTO_INCREMENT=16966 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `query_new`
--

DROP TABLE IF EXISTS `query_new`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `query_new` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `log_key` varchar(30) NOT NULL,
  `log_type` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `select` varchar(200) NOT NULL,
  `where` varchar(500) NOT NULL,
  `group` varchar(50) NOT NULL,
  `order` varchar(20) NOT NULL,
  `order_type` int(11) NOT NULL,
  `sql` longtext NOT NULL,
  `create_time` datetime NOT NULL,
  `cache_validate` int(11) DEFAULT NULL,
  `remark` varchar(1000) NOT NULL,
  `_field_config` longtext NOT NULL,
  `template_name` varchar(32) DEFAULT '',
  `other_sql` text,
  PRIMARY KEY (`id`),
  KEY `query_new_43586ea` (`log_key`),
  KEY `query_new_40194370` (`log_key`)
) ENGINE=InnoDB AUTO_INCREMENT=806 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `query_result`
--

DROP TABLE IF EXISTS `query_result`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `query_result` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `remark` varchar(200) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `query_result_statistic`
--

DROP TABLE IF EXISTS `query_result_statistic`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `query_result_statistic` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `queryresult_id` int(11) NOT NULL,
  `statistic_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `queryresult_id` (`queryresult_id`,`statistic_id`),
  KEY `query_result_statistic_b0a0b2b0` (`queryresult_id`),
  KEY `query_result_statistic_df6b1bf0` (`statistic_id`),
  CONSTRAINT `queryresult_id_refs_id_963c7f96` FOREIGN KEY (`queryresult_id`) REFERENCES `query_result` (`id`),
  CONSTRAINT `statistic_id_refs_id_fe1caaee` FOREIGN KEY (`statistic_id`) REFERENCES `statistic_new` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `question`
--

DROP TABLE IF EXISTS `question`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `question` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `server_id` int(11) NOT NULL,
  `channel_id` int(11) NOT NULL,
  `question_type` int(11) NOT NULL,
  `status` int(11) NOT NULL,
  `question` varchar(400) NOT NULL,
  `answer` varchar(400) NOT NULL,
  `post_time` datetime NOT NULL,
  `reply_time` datetime DEFAULT NULL,
  `post_user` int(11) NOT NULL,
  `post_user_id` int(11) NOT NULL,
  `score` int(11) NOT NULL,
  `reply_user` varchar(20) NOT NULL,
  `category` varchar(100) NOT NULL,
  `info` varchar(1000) NOT NULL,
  `check_time` datetime DEFAULT NULL,
  `order_time` datetime DEFAULT NULL,
  `order_user` varchar(20) NOT NULL,
  `session_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `question_eb822f1d` (`server_id`),
  KEY `question_69a8080e` (`channel_id`),
  KEY `question_48fb58bb` (`status`),
  KEY `question_fdd15200` (`post_time`),
  KEY `question_215f161e` (`reply_time`),
  KEY `question_f7eefd1d` (`post_user`),
  KEY `question_931001d3` (`post_user_id`),
  KEY `question_7c5c8902` (`score`),
  KEY `question_b12fa840` (`reply_user`),
  KEY `question_6f33f001` (`category`),
  KEY `question_83615d3f` (`check_time`),
  KEY `question_8a65fca5` (`order_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `question_other`
--

DROP TABLE IF EXISTS `question_other`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `question_other` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `qid` int(11) NOT NULL,
  `type` int(11) NOT NULL,
  `data` longtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `question_other_8b2b9fbe` (`qid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `rebate_user`
--

DROP TABLE IF EXISTS `rebate_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rebate_user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(128) NOT NULL,
  `rebate_status` int(11) NOT NULL,
  `expire_time` datetime NOT NULL,
  `server_id` int(11) NOT NULL,
  `last_time` datetime NOT NULL,
  `pay_reward` int(11) NOT NULL,
  `login_reward` int(11) NOT NULL,
  `other_reward` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `rebate_user_ee0cafa2` (`username`),
  KEY `rebate_user_8bbef8ad` (`expire_time`),
  KEY `rebate_user_eb822f1d` (`server_id`)
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
) ENGINE=InnoDB AUTO_INCREMENT=246 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `result`
--

DROP TABLE IF EXISTS `result`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `result` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `statistic_id` int(11) NOT NULL,
  `server_id` int(11) NOT NULL,
  `channel_id` int(11) NOT NULL,
  `tag` int(11) NOT NULL,
  `result` double NOT NULL,
  `create_time` datetime NOT NULL,
  `result_time` datetime NOT NULL,
  PRIMARY KEY (`id`)
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
) ENGINE=InnoDB AUTO_INCREMENT=36 DEFAULT CHARSET=utf8;
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
) ENGINE=InnoDB AUTO_INCREMENT=246 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `safe_question`
--

DROP TABLE IF EXISTS `safe_question`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `safe_question` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `question` varchar(100) NOT NULL,
  `answer` varchar(100) NOT NULL,
  `create_time` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `safe_question_6340c63c` (`user_id`),
  KEY `safe_question_7952171b` (`create_time`),
  CONSTRAINT `user_id_refs_id_22f0f98d` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
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
  `name` varchar(50) DEFAULT NULL,
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
  `last_time` datetime NOT NULL,
  `tabId` int(10) DEFAULT NULL,
  `game_data` varchar(1000) DEFAULT NULL,
  `game_db_addr_port` varchar(100) DEFAULT NULL,
  `game_db_name` varchar(100) DEFAULT NULL,
  `game_db_user` varchar(100) DEFAULT NULL,
  `game_db_password` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3554 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `statistic_new`
--

DROP TABLE IF EXISTS `statistic_new`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `statistic_new` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `log_type` int(11) NOT NULL,
  `count_type` int(11) NOT NULL,
  `name` varchar(200) NOT NULL,
  `field_name` varchar(50) NOT NULL,
  `where` varchar(50) NOT NULL,
  `sql` varchar(5000) DEFAULT NULL,
  `exec_interval` int(11) NOT NULL,
  `last_exec_time` datetime DEFAULT NULL,
  `is_auto_execute` int(11) NOT NULL,
  `auto_exec_interval` int(11) NOT NULL,
  `remark` varchar(1000) DEFAULT NULL,
  `result_data` varchar(200) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=69 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `upgrade`
--

DROP TABLE IF EXISTS `upgrade`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `upgrade` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ver_num` int(11) NOT NULL,
  `ver_name` varchar(20) NOT NULL,
  `filesize` varchar(10) NOT NULL,
  `client_ver` varchar(50) NOT NULL,
  `min_client_ver` varchar(50) NOT NULL,
  `download_url` varchar(500) NOT NULL,
  `ios_url` varchar(500) NOT NULL,
  `android_url` varchar(500) NOT NULL,
  `increment_url` varchar(500) NOT NULL,
  `subpackage_url` varchar(500) NOT NULL,
  `md5_num` varchar(500) NOT NULL,
  `page_url` varchar(500) NOT NULL,
  `remark` varchar(500) NOT NULL,
  `create_time` datetime NOT NULL,
  `pub_ip` varchar(20) NOT NULL,
  `pub_user` int(11) NOT NULL,
  `notice_switch` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `upgrade_278b5eba` (`pub_user`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `upgrade_channel`
--

DROP TABLE IF EXISTS `upgrade_channel`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `upgrade_channel` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `upgrade_id` int(11) NOT NULL,
  `channel_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `upgrade_id` (`upgrade_id`,`channel_id`),
  KEY `upgrade_channel_403ca1b0` (`upgrade_id`),
  KEY `upgrade_channel_9e85bf2d` (`channel_id`),
  CONSTRAINT `channel_id_refs_id_23ff0f6c` FOREIGN KEY (`channel_id`) REFERENCES `channel` (`id`),
  CONSTRAINT `upgrade_id_refs_id_9ca14ba0` FOREIGN KEY (`upgrade_id`) REFERENCES `upgrade` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `upgrade_group`
--

DROP TABLE IF EXISTS `upgrade_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `upgrade_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `upgrade_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `upgrade_id` (`upgrade_id`,`group_id`),
  KEY `upgrade_group_403ca1b0` (`upgrade_id`),
  KEY `upgrade_group_5f412f9a` (`group_id`),
  CONSTRAINT `group_id_refs_id_c1a5ff02` FOREIGN KEY (`group_id`) REFERENCES `groups` (`id`),
  CONSTRAINT `upgrade_id_refs_id_9b0f9f4a` FOREIGN KEY (`upgrade_id`) REFERENCES `upgrade` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_type`
--

DROP TABLE IF EXISTS `user_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(32) NOT NULL,
  `type_id` int(11) NOT NULL,
  `func_name` varchar(20) NOT NULL,
  `func_ver` int(11) NOT NULL,
  `login_config` varchar(1000) DEFAULT NULL,
  `remark` varchar(200) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(128) DEFAULT NULL,
  `password` varchar(32) NOT NULL,
  `user_type` int(11) NOT NULL,
  `link_key` varchar(50) NOT NULL,
  `create_time` datetime NOT NULL,
  `last_time` datetime NOT NULL,
  `last_ip` varchar(32) NOT NULL,
  `last_key` varchar(50) DEFAULT NULL,
  `last_server` varchar(50) DEFAULT NULL,
  `login_num` int(11) NOT NULL,
  `lock_time` datetime DEFAULT NULL,
  `login_count` int(11) NOT NULL,
  `status` int(11) NOT NULL,
  `channel_key` varchar(50) DEFAULT NULL,
  `mobile_key` varchar(50) NOT NULL,
  `other` varchar(500) DEFAULT NULL,
  `recharge_status` int(11) DEFAULT NULL,
  `other_data` varchar(1000) DEFAULT NULL,
  `clientId` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `users_ee0cafa2` (`username`),
  KEY `users_f96a0352` (`user_type`),
  KEY `users_acd89b05` (`link_key`),
  KEY `users_7952171b` (`create_time`),
  KEY `users_6aae6f5d` (`last_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `users_info`
--

DROP TABLE IF EXISTS `users_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users_info` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_type` int(11) NOT NULL,
  `channel_id` varchar(20) NOT NULL,
  `link_key` varchar(50) NOT NULL,
  `info` longtext,
  PRIMARY KEY (`id`),
  KEY `users_info_f96a0352` (`user_type`),
  KEY `users_info_69a8080e` (`channel_id`),
  KEY `users_info_acd89b05` (`link_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `viplist`
--

DROP TABLE IF EXISTS `viplist`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `viplist` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `player_id` int(11) NOT NULL,
  `server_id` int(11) NOT NULL,
  `privilege_type` int(11) NOT NULL,
  `everyday_type` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `viplist_5ef042d9` (`player_id`),
  KEY `viplist_eb822f1d` (`server_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `voice`
--

DROP TABLE IF EXISTS `voice`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `voice` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `player_id` int(11) NOT NULL,
  `server_id` int(11) NOT NULL,
  `channel_id` int(11) NOT NULL,
  `voice_path` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `voice_5ef042d9` (`player_id`),
  KEY `voice_eb822f1d` (`server_id`),
  KEY `voice_69a8080e` (`channel_id`)
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

-- Dump completed on 2019-01-31 11:52:29

CREATE TABLE operation_activity (
  id INT unsigned AUTO_INCREMENT PRIMARY KEY,
  sid INT unsigned,
  server VARCHAR(2000),
  activityId INT unsigned,
  icon VARCHAR(50),
  backIcon1 VARCHAR(50),
  backIcon2 VARCHAR(50),
  titleIcon VARCHAR(50),
  shopIcon VARCHAR(50),
  enterIcon VARCHAR(50),
  name VARCHAR(50),
  content VARCHAR(500),
  imageIcon VARCHAR(50),
  imageContent VARCHAR(500),
  imageScore VARCHAR(50),
  eventActivityRankAwardList VARCHAR(2000),
  startTime DATETIME,
  endTime DATETIME,
  endRewardTime DATETIME,
  status INT,
  auditor INT unsigned
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

commit;