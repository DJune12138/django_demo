--  CREATE DATABASE IF NOT EXISTS test123 default charset utf8 COLLATE utf8_unicode_ci;
--  DROP TABLE IF EXISTS log_0_new ;
--  CREATE TABLE IF NOT EXISTS `log_0_new` (
--      `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
--      `log_time` datetime NOT NULL,
--      `log_type` integer NOT NULL,
--      `log_tag` integer,
--      `log_user` integer,
--      `log_name` varchar(100),
--      `log_server` integer,
--      `log_level` integer,
--      `log_previous` varchar(200),
--      `log_now` varchar(200),
--      `log_relate` varchar(32),
--      `f1` varchar(100),
--      `f2` varchar(100),
--      `f3` varchar(100),
--      `f4` varchar(100),
--      `f5` varchar(100),
--      `f6` longtext,
--      `f7` varchar(100),
--      `f8` longtext,
--      `log_channel` integer,
--      `log_data` integer,
--      `log_result` integer
--  )
--   ENGINE=InnoDB ;
CREATE TABLE IF NOT EXISTS  log_statistic_date LIKE log_0_new;
CREATE INDEX `log_statistic_date_log_time_index` ON `log_statistic_date` (log_time);

--  创建存储过程
DROP PROCEDURE IF EXISTS InsertLogStatisticDate;

--  这里前面两个$$ 用mysqldb时是去掉的
delimiter $$

create procedure InsertLogStatisticDate()
begin
 declare sdate NVARCHAR(20);
 declare tol_num INT;
 set @sdate='2000-01-01 00:00:00';
 set @tol_num=(select count(0) from log_statistic_date);
 if @tol_num = 0 then 
     set autocommit=0;
     while @sdate<'2100-01-01 00:00:00' do
        INSERT INTO log_statistic_date(log_time) values(@sdate);
        set @sdate=date_add(@sdate,interval 1 hour);
     end while;
     commit;
     set autocommit=1;
 end if;
end $$ 

delimiter ;

call InsertLogStatisticDate;
