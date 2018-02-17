ALTER TABLE `ems`.`experimenttype` DROP COLUMN `template`, DROP COLUMN `workflow`;
ALTER TABLE `ems`.`experimenttype` DROP COLUMN `upload_rules`;

ALTER TABLE `ems`.`experimenttype`
ADD workflow VARCHAR(255) CHARACTER SET utf8,
ADD template TEXT CHARACTER SET utf8,
ADD upload_rules TEXT CHARACTER SET utf8;


