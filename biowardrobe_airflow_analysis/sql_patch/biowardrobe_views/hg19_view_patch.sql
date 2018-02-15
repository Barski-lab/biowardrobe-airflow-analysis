DROP VIEW IF EXISTS `hg19`.`trackDb_local`;
CREATE VIEW `hg19`.`trackDb_local` AS
SELECT replace(concat(`l`.`uid`,'_wtrack'),'-','_') AS `tableName`,
       `l`.`name4browser` AS `shortLabel`,
       if((`et`.`etype` LIKE '%dUTP%'),'PbedGraph 4','bedGraph 4') AS `type`,
       `l`.`name4browser` AS `longLabel`,
       0 AS `visibility`,
       10 AS `priority`,
       30 AS `colorR`,
       70 AS `colorG`,
       150 AS `colorB`,
       30 AS `altColorR`,
       70 AS `altColorG`,
       150 AS `altColorB`,
       0 AS `useScore`,
       0 AS `private`,
       0 AS `restrictCount`,
       NULL AS `restrictList`,
       NULL AS `url`,
       NULL AS `html`,
       `l`.`egroup_id` AS `grp`,
       0 AS `canPack`,
       'autoScale on
       windowingFunction maximum' AS `settings`
FROM ((`ems`.`labdata` `l`
       JOIN `ems`.`experimenttype` `et`)
       JOIN `ems`.`genome` `g`)
WHERE ((`l`.`deleted` = 0)
       AND (`l`.`libstatus` BETWEEN 10 AND 99)
       AND (`l`.`experimenttype_id` = `et`.`id`)
       AND (`et`.`etype` LIKE '%RNA%')
       AND (`l`.`genome_id` = `g`.`id`)
       AND (`l`.`egroup_id` IS NOT NULL)
       AND (`g`.`db` LIKE 'hg%'))
UNION
SELECT replace(concat(`l`.`uid`,'_f_wtrack'),'-','_') AS `tableName`,
       `l`.`name4browser` AS `shortLabel`,
       'bigWig' AS `type`,
       `l`.`name4browser` AS `longLabel`,
       0 AS `visibility`,
       2 AS `priority`,
       30 AS `colorR`,
       70 AS `colorG`,
       150 AS `colorB`,
       30 AS `altColorR`,
       70 AS `altColorG`,
       150 AS `altColorB`,
       0 AS `useScore`,
       0 AS `private`,
       0 AS `restrictCount`,
       NULL AS `restrictList`,
       NULL AS `url`,
       NULL AS `html`,
       `l`.`egroup_id` AS `grp`,
       0 AS `canPack`,
       concat('track ',replace(concat(`l`.`uid`,'_f_wtrack'),'-','_'),'
               autoScale on
               visibility hide
               windowingFunction maximum') AS `settings`
FROM ((`ems`.`labdata` `l`
       JOIN `ems`.`experimenttype` `et`)
       JOIN `ems`.`genome` `g`)
WHERE ((`l`.`deleted` = 0)
       AND (`l`.`libstatus` BETWEEN 10 AND 99)
       AND (`l`.`experimenttype_id` = `et`.`id`)
       AND (`et`.`etype` LIKE '%RNA%')
       AND (`et`.`etype` NOT LIKE '%dUTP%')
       AND (`l`.`genome_id` = `g`.`id`)
       AND (`l`.`egroup_id` IS NOT NULL)
       AND (`g`.`db` LIKE 'hg%'))
UNION
SELECT replace(concat(`l`.`uid`,'_multi_f_wtrack'),'-','_') AS `tableName`,
       `l`.`name4browser` AS `shortLabel`,
       'bigWig' AS `type`,
       `l`.`name4browser` AS `longLabel`,
       0 AS `visibility`,
       2 AS `priority`,
       30 AS `colorR`,
       70 AS `colorG`,
       150 AS `colorB`,
       30 AS `altColorR`,
       70 AS `altColorG`,
       150 AS `altColorB`,
       0 AS `useScore`,
       0 AS `private`,
       0 AS `restrictCount`,
       NULL AS `restrictList`,
       NULL AS `url`,
       NULL AS `html`,
       `l`.`egroup_id` AS `grp`,
       0 AS `canPack`,
       concat('track ',replace(concat(`l`.`uid`,'_multi_f_wtrack'),'-','_'),'
               group ',`l`.`egroup_id`,'
               container multiWig
               autoScale on
               visibility hide
               windowingFunction maximum') AS `settings`
FROM ((`ems`.`labdata` `l`
       JOIN `ems`.`experimenttype` `et`)
       JOIN `ems`.`genome` `g`)
WHERE ((`l`.`deleted` = 0)
       AND (`l`.`libstatus` BETWEEN 10 AND 99)
       AND (`l`.`experimenttype_id` = `et`.`id`)
       AND (`et`.`etype` LIKE '%RNA%dUTP%')
       AND (`l`.`genome_id` = `g`.`id`)
       AND (`l`.`egroup_id` IS NOT NULL)
       AND (`g`.`db` LIKE 'hg%'))
UNION
SELECT replace(concat(`l`.`uid`,'_upstream_f_wtrack'),'-','_') AS `tableName`,
       `l`.`name4browser` AS `shortLabel`,
       'bigWig' AS `type`,
       `l`.`name4browser` AS `longLabel`,
       0 AS `visibility`,
       2 AS `priority`,
       30 AS `colorR`,
       70 AS `colorG`,
       150 AS `colorB`,
       30 AS `altColorR`,
       150 AS `altColorG`,
       70 AS `altColorB`,
       0 AS `useScore`,
       0 AS `private`,
       0 AS `restrictCount`,
       NULL AS `restrictList`,
       NULL AS `url`,
       NULL AS `html`,
       `l`.`egroup_id` AS `grp`,
       0 AS `canPack`,
       concat('track ',replace(concat(`l`.`uid`,'_upstream_f_wtrack'),'-','_'),'
               parent ',replace(concat(`l`.`uid`,'_multi_f_wtrack'),'-','_')) AS `settings`
FROM ((`ems`.`labdata` `l`
       JOIN `ems`.`experimenttype` `et`)
       JOIN `ems`.`genome` `g`)
WHERE ((`l`.`deleted` = 0)
       AND (`l`.`libstatus` BETWEEN 10 AND 99)
       AND (`l`.`experimenttype_id` = `et`.`id`)
       AND (`et`.`etype` LIKE '%RNA%dUTP%')
       AND (`l`.`genome_id` = `g`.`id`)
       AND (`l`.`egroup_id` IS NOT NULL)
       AND (`g`.`db` LIKE 'hg%'))
UNION
SELECT replace(concat(`l`.`uid`,'_downstream_f_wtrack'),'-','_') AS `tableName`,
       `l`.`name4browser` AS `shortLabel`,
       'bigWig' AS `type`,
       `l`.`name4browser` AS `longLabel`,
       0 AS `visibility`,
       2 AS `priority`,
       30 AS `colorR`,
       70 AS `colorG`,
       150 AS `colorB`,
       30 AS `altColorR`,
       150 AS `altColorG`,
       70 AS `altColorB`,
       0 AS `useScore`,
       0 AS `private`,
       0 AS `restrictCount`,
       NULL AS `restrictList`,
       NULL AS `url`,
       NULL AS `html`,
       `l`.`egroup_id` AS `grp`,
       0 AS `canPack`,
       concat('track ',replace(concat(`l`.`uid`,'_downstream_f_wtrack'),'-','_'),'
               parent ',replace(concat(`l`.`uid`,'_multi_f_wtrack'),'-','_')) AS `settings`
FROM ((`ems`.`labdata` `l`
       JOIN `ems`.`experimenttype` `et`)
       JOIN `ems`.`genome` `g`)
WHERE ((`l`.`deleted` = 0)
       AND (`l`.`libstatus` BETWEEN 10 AND 99)
       AND (`l`.`experimenttype_id` = `et`.`id`)
       AND (`et`.`etype` LIKE '%RNA%dUTP%')
       AND (`l`.`genome_id` = `g`.`id`)
       AND (`l`.`egroup_id` IS NOT NULL)
       AND (`g`.`db` LIKE 'hg%'))
UNION
SELECT replace(concat(`l`.`uid`,'_grp'),'-','_') AS `tableName`,
       `l`.`name4browser` AS `shortLabel`,
       'bed 4 +' AS `type`,
       `l`.`name4browser` AS `longLabel`,
       0 AS `visibility`,
       10 AS `priority`,
       30 AS `colorR`,
       70 AS `colorG`,
       150 AS `colorB`,
       30 AS `altColorR`,
       70 AS `altColorG`,
       150 AS `altColorB`,
       0 AS `useScore`,
       0 AS `private`,
       0 AS `restrictCount`,
       NULL AS `restrictList`,
       NULL AS `url`,
       NULL AS `html`,
       `l`.`egroup_id` AS `grp`,
       0 AS `canPack`,
       concat('compositeTrack on
               visibility hide
               subGroup1 view Views GCVRG=GenomeCoverage ILNDS=Islands
               group ',`l`.`egroup_id`,'
               track ',replace(concat(`l`.`uid`,'_grp'),'-','_'),'') AS `settings`
FROM ((`ems`.`labdata` `l`
       JOIN `ems`.`experimenttype` `et`)
       JOIN `ems`.`genome` `g`)
WHERE ((`l`.`deleted` = 0)
       AND (`l`.`libstatus` BETWEEN 10 AND 99)
       AND (`l`.`experimenttype_id` = `et`.`id`)
       AND (`et`.`etype` LIKE '%DNA%')
       AND (`l`.`genome_id` = `g`.`id`)
       AND (`l`.`egroup_id` IS NOT NULL)
       AND (`g`.`db` LIKE 'hg%'))
UNION
SELECT replace(concat(`l`.`uid`,'_gcvrg'),'-','_') AS `tableName`,
       `l`.`name4browser` AS `shortLabel`,
       'bedGraph 4' AS `type`,
       `l`.`name4browser` AS `longLabel`,
       2 AS `visibility`,
       1 AS `priority`,
       30 AS `colorR`,
       70 AS `colorG`,
       150 AS `colorB`,
       30 AS `altColorR`,
       70 AS `altColorG`,
       150 AS `altColorB`,
       0 AS `useScore`,
       0 AS `private`,
       0 AS `restrictCount`,
       NULL AS `restrictList`,
       NULL AS `url`,
       NULL AS `html`,
       `l`.`egroup_id` AS `grp`,
       0 AS `canPack`,
       concat('parent ',replace(concat(`l`.`uid`,'_grp'),'-','_'),'
               track ',replace(concat(`l`.`uid`,'_gcvrg'),'-','_'),'
               view GCVRG
               visibility full') AS `settings`
FROM ((`ems`.`labdata` `l`
       JOIN `ems`.`experimenttype` `et`)
       JOIN `ems`.`genome` `g`)
WHERE ((`l`.`deleted` = 0)
       AND (`l`.`libstatus` BETWEEN 10 AND 99)
       AND (`l`.`experimenttype_id` = `et`.`id`)
       AND (`et`.`etype` LIKE '%DNA%')
       AND (`l`.`genome_id` = `g`.`id`)
       AND (`l`.`egroup_id` IS NOT NULL)
       AND (`g`.`db` LIKE 'hg%'))
UNION
SELECT replace(concat(`l`.`uid`,'_ilnds'),'-','_') AS `tableName`,
       `l`.`name4browser` AS `shortLabel`,
       'bed 4 +' AS `type`,
       `l`.`name4browser` AS `longLabel`,
       1 AS `visibility`,
       1 AS `priority`,
       30 AS `colorR`,
       70 AS `colorG`,
       150 AS `colorB`,
       30 AS `altColorR`,
       70 AS `altColorG`,
       150 AS `altColorB`,
       0 AS `useScore`,
       0 AS `private`,
       0 AS `restrictCount`,
       NULL AS `restrictList`,
       NULL AS `url`,
       NULL AS `html`,
       `l`.`egroup_id` AS `grp`,
       0 AS `canPack`,
       concat('parent ',replace(concat(`l`.`uid`,'_grp'),'-','_'),'
               track ',replace(concat(`l`.`uid`,'_ilnds'),'-','_'),'
               view ILNDS
               visibility dense') AS `settings`
FROM ((`ems`.`labdata` `l`
       JOIN `ems`.`experimenttype` `et`)
      JOIN `ems`.`genome` `g`)
WHERE ((`l`.`deleted` = 0)
       AND (`l`.`libstatus` BETWEEN 10 AND 99)
       AND (`l`.`experimenttype_id` = `et`.`id`)
       AND (`et`.`etype` LIKE '%DNA%')
       AND (`l`.`genome_id` = `g`.`id`)
       AND (`l`.`egroup_id` IS NOT NULL)
       AND (`g`.`db` LIKE 'hg%'))
UNION
SELECT replace(concat(`l`.`uid`,'_wtrack'),'-','_') AS `tableName`,
       `l`.`name4browser` AS `shortLabel`,
       'bedGraph 4' AS `type`,
       `l`.`name4browser` AS `longLabel`,
       2 AS `visibility`,
       1 AS `priority`,
       30 AS `colorR`,
       70 AS `colorG`,
       150 AS `colorB`,
       30 AS `altColorR`,
       70 AS `altColorG`,
       150 AS `altColorB`,
       0 AS `useScore`,
       0 AS `private`,
       0 AS `restrictCount`,
       NULL AS `restrictList`,
       NULL AS `url`,
       NULL AS `html`,
       `l`.`egroup_id` AS `grp`,
       0 AS `canPack`,
       concat('parent ',replace(concat(`l`.`uid`,'_gcvrg'),'-','_'),'
               track ',replace(concat(`l`.`uid`,'_wtrack'),'-','_'),'
               subGroups view=GCVRG
               autoScale on
               visibility full
               windowingFunction maximum') AS `settings`
FROM ((`ems`.`labdata` `l`
       JOIN `ems`.`experimenttype` `et`)
       JOIN `ems`.`genome` `g`)
WHERE ((`l`.`deleted` = 0)
       AND (`l`.`libstatus` BETWEEN 10 AND 99)
       AND (`l`.`experimenttype_id` = `et`.`id`)
       AND (`et`.`etype` LIKE '%DNA%')
       AND (`l`.`genome_id` = `g`.`id`)
       AND (`l`.`egroup_id` IS NOT NULL)
       AND (`g`.`db` LIKE 'hg%'))
UNION
SELECT replace(concat(`l`.`uid`,'_islands'),'-','_') AS `tableName`,
       `l`.`name4browser` AS `shortLabel`,
       'bed 4 +' AS `type`,
       `l`.`name4browser` AS `longLabel`,
       1 AS `visibility`,
       3 AS `priority`,
       0 AS `colorR`,
       30 AS `colorG`,
       100 AS `colorB`,
       30 AS `altColorR`,
       70 AS `altColorG`,
       150 AS `altColorB`,
       0 AS `useScore`,
       0 AS `private`,
       0 AS `restrictCount`,
       NULL AS `restrictList`,
       NULL AS `url`,
       NULL AS `html`,
       `l`.`egroup_id` AS `grp`,
       1 AS `canPack`,
       concat('parent ',replace(concat(`l`.`uid`,'_ilnds'),'-','_'),'
               track ',replace(concat(`l`.`uid`,'_islands'),'-','_'),'
               subGroups view=ILNDS
               visibility dense') AS `settings`
FROM ((`ems`.`labdata` `l`
       JOIN `ems`.`experimenttype` `et`)
       JOIN `ems`.`genome` `g`)
WHERE ((`l`.`deleted` = 0)
       AND (`l`.`libstatus` BETWEEN 10 AND 99)
       AND (`l`.`experimenttype_id` = `et`.`id`)
       AND (`et`.`etype` LIKE '%DNA%')
       AND (`l`.`genome_id` = `g`.`id`)
       AND (`l`.`egroup_id` IS NOT NULL)
       AND (`g`.`db` LIKE 'hg%'))
UNION
SELECT replace(concat(`l`.`uid`,'_f_wtrack'),'-','_') AS `tableName`,
       `l`.`name4browser` AS `shortLabel`,
       'bigWig' AS `type`,
       `l`.`name4browser` AS `longLabel`,
       2 AS `visibility`,
       2 AS `priority`,
       30 AS `colorR`,
       70 AS `colorG`,
       150 AS `colorB`,
       30 AS `altColorR`,
       70 AS `altColorG`,
       150 AS `altColorB`,
       0 AS `useScore`,
       0 AS `private`,
       0 AS `restrictCount`,
       NULL AS `restrictList`,
       NULL AS `url`,
       NULL AS `html`,
       `l`.`egroup_id` AS `grp`,
       0 AS `canPack`,
       concat('parent ',replace(concat(`l`.`uid`,'_gcvrg'),'-','_'),'
               track ',replace(concat(`l`.`uid`,'_f_wtrack'),'-','_'),'
               subGroups view=GCVRG
               autoScale on
               visibility full
               windowingFunction maximum') AS `settings`
FROM ((`ems`.`labdata` `l`
       JOIN `ems`.`experimenttype` `et`)
       JOIN `ems`.`genome` `g`)
WHERE ((`l`.`deleted` = 0)
       AND (`l`.`libstatus` BETWEEN 10 AND 99)
       AND (`l`.`experimenttype_id` = `et`.`id`)
       AND (`et`.`etype` LIKE '%DNA%')
       AND (`l`.`genome_id` = `g`.`id`)
       AND (`l`.`egroup_id` IS NOT NULL)
       AND (`g`.`db` LIKE 'hg%'))