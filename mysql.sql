
CREATE TABLE beauty_user_behavior (
    user_id VARCHAR(50),  -- 用户ID（脱敏后为字符串，用VARCHAR兼容）
    item_id VARCHAR(50),  -- 商品ID（同理用VARCHAR）
    behavior_type INT,    -- 行为类型（1浏览/2收藏/3加购/4购买，整数类型）
    item_category VARCHAR(50),  -- 商品品类ID
    date VARCHAR(20),     -- 日期（格式：2023-12-06）
    hour INT,             -- 小时（0-23）
    user_geohash VARCHAR(50)  -- 省份
);

LOAD DATA LOCAL INFILE '"C:/Mysql/beautydata.csv"'
INTO TABLE beauty_data.beauty_user_behavior
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS;   -- 如果 CSV 第一行是列名

SET GLOBAL local_infile = 1;