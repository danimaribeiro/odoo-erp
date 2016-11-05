drop table if exists finan_conta_arvore;

create table finan_conta_arvore as

SELECT
    c1.id AS conta_pai_id,
    c1.id AS conta_id,
    CASE
        WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
        ELSE 1
    END AS redutora,
    1 as nivel
   FROM finan_conta c1
  WHERE coalesce(c1.sintetica, False) = false
UNION ALL
 SELECT c2.id AS conta_pai_id,
    c1.id AS conta_id,
        CASE
            WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
            ELSE 1
        END AS redutora,
    2 as nivel
   FROM finan_conta c1
     JOIN finan_conta c2 ON c2.id = c1.parent_id
  WHERE coalesce(c1.sintetica, False) = false
UNION ALL
 SELECT c3.id AS conta_pai_id,
    c1.id AS conta_id,
        CASE
            WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
            ELSE 1
        END AS redutora,
    3 as nivel
   FROM finan_conta c1
     JOIN finan_conta c2 ON c2.id = c1.parent_id
     JOIN finan_conta c3 ON c3.id = c2.parent_id
  WHERE coalesce(c1.sintetica, False) = false
UNION ALL
 SELECT c4.id AS conta_pai_id,
    c1.id AS conta_id,
        CASE
            WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
            ELSE 1
        END AS redutora,
    4 as nivel
   FROM finan_conta c1
     JOIN finan_conta c2 ON c2.id = c1.parent_id
     JOIN finan_conta c3 ON c3.id = c2.parent_id
     JOIN finan_conta c4 ON c4.id = c3.parent_id
  WHERE coalesce(c1.sintetica, False) = false
UNION ALL
 SELECT c5.id AS conta_pai_id,
    c1.id AS conta_id,
        CASE
            WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
            ELSE 1
        END AS redutora,
    5 as nivel
   FROM finan_conta c1
     JOIN finan_conta c2 ON c2.id = c1.parent_id
     JOIN finan_conta c3 ON c3.id = c2.parent_id
     JOIN finan_conta c4 ON c4.id = c3.parent_id
     JOIN finan_conta c5 ON c5.id = c4.parent_id
  WHERE coalesce(c1.sintetica, False) = false
UNION ALL
 SELECT c6.id AS conta_pai_id,
    c1.id AS conta_id,
        CASE
            WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
            ELSE 1
        END AS redutora,
    6 as nivel
   FROM finan_conta c1
     JOIN finan_conta c2 ON c2.id = c1.parent_id
     JOIN finan_conta c3 ON c3.id = c2.parent_id
     JOIN finan_conta c4 ON c4.id = c3.parent_id
     JOIN finan_conta c5 ON c5.id = c4.parent_id
     JOIN finan_conta c6 ON c6.id = c5.parent_id
  WHERE coalesce(c1.sintetica, False) = false
UNION ALL
 SELECT c7.id AS conta_pai_id,
    c1.id AS conta_id,
        CASE
            WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
            ELSE 1
        END AS redutora,
    7 as nivel
   FROM finan_conta c1
     JOIN finan_conta c2 ON c2.id = c1.parent_id
     JOIN finan_conta c3 ON c3.id = c2.parent_id
     JOIN finan_conta c4 ON c4.id = c3.parent_id
     JOIN finan_conta c5 ON c5.id = c4.parent_id
     JOIN finan_conta c6 ON c6.id = c5.parent_id
     JOIN finan_conta c7 ON c7.id = c6.parent_id
  WHERE coalesce(c1.sintetica, False) = false

UNION ALL
 SELECT c8.id AS conta_pai_id,
    c1.id AS conta_id,
        CASE
            WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
            ELSE 1
        END AS redutora,
    8 as nivel
   FROM finan_conta c1
     JOIN finan_conta c2 ON c2.id = c1.parent_id
     JOIN finan_conta c3 ON c3.id = c2.parent_id
     JOIN finan_conta c4 ON c4.id = c3.parent_id
     JOIN finan_conta c5 ON c5.id = c4.parent_id
     JOIN finan_conta c6 ON c6.id = c5.parent_id
     JOIN finan_conta c7 ON c7.id = c6.parent_id
     JOIN finan_conta c8 ON c8.id = c7.parent_id
  WHERE coalesce(c1.sintetica, False) = false

UNION ALL
 SELECT c9.id AS conta_pai_id,
    c1.id AS conta_id,
        CASE
            WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
            ELSE 1
        END AS redutora,
    9 as nivel
   FROM finan_conta c1
     JOIN finan_conta c2 ON c2.id = c1.parent_id
     JOIN finan_conta c3 ON c3.id = c2.parent_id
     JOIN finan_conta c4 ON c4.id = c3.parent_id
     JOIN finan_conta c5 ON c5.id = c4.parent_id
     JOIN finan_conta c6 ON c6.id = c5.parent_id
     JOIN finan_conta c7 ON c7.id = c6.parent_id
     JOIN finan_conta c8 ON c8.id = c7.parent_id
     JOIN finan_conta c9 ON c9.id = c8.parent_id
  WHERE coalesce(c1.sintetica, False) = false

UNION ALL
 SELECT c10.id AS conta_pai_id,
    c1.id AS conta_id,
        CASE
            WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
            ELSE 1
        END AS redutora,
    10 as nivel
   FROM finan_conta c1
     JOIN finan_conta c2 ON c2.id = c1.parent_id
     JOIN finan_conta c3 ON c3.id = c2.parent_id
     JOIN finan_conta c4 ON c4.id = c3.parent_id
     JOIN finan_conta c5 ON c5.id = c4.parent_id
     JOIN finan_conta c6 ON c6.id = c5.parent_id
     JOIN finan_conta c7 ON c7.id = c6.parent_id
     JOIN finan_conta c8 ON c8.id = c7.parent_id
     JOIN finan_conta c9 ON c9.id = c8.parent_id
     JOIN finan_conta c10 ON c10.id = c9.parent_id
  WHERE coalesce(c1.sintetica, False) = false

UNION ALL
 SELECT c11.id AS conta_pai_id,
    c1.id AS conta_id,
        CASE
            WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
            ELSE 1
        END AS redutora,
    11 as nivel
   FROM finan_conta c1
     JOIN finan_conta c2 ON c2.id = c1.parent_id
     JOIN finan_conta c3 ON c3.id = c2.parent_id
     JOIN finan_conta c4 ON c4.id = c3.parent_id
     JOIN finan_conta c5 ON c5.id = c4.parent_id
     JOIN finan_conta c6 ON c6.id = c5.parent_id
     JOIN finan_conta c7 ON c7.id = c6.parent_id
     JOIN finan_conta c8 ON c8.id = c7.parent_id
     JOIN finan_conta c9 ON c9.id = c8.parent_id
     JOIN finan_conta c10 ON c10.id = c9.parent_id
     JOIN finan_conta c11 ON c11.id = c10.parent_id
  WHERE coalesce(c1.sintetica, False) = false


UNION ALL
 SELECT c12.id AS conta_pai_id,
    c1.id AS conta_id,
        CASE
            WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
            ELSE 1
        END AS redutora,
    12 as nivel
   FROM finan_conta c1
     JOIN finan_conta c2 ON c2.id = c1.parent_id
     JOIN finan_conta c3 ON c3.id = c2.parent_id
     JOIN finan_conta c4 ON c4.id = c3.parent_id
     JOIN finan_conta c5 ON c5.id = c4.parent_id
     JOIN finan_conta c6 ON c6.id = c5.parent_id
     JOIN finan_conta c7 ON c7.id = c6.parent_id
     JOIN finan_conta c8 ON c8.id = c7.parent_id
     JOIN finan_conta c9 ON c9.id = c8.parent_id
     JOIN finan_conta c10 ON c10.id = c9.parent_id
     JOIN finan_conta c11 ON c11.id = c10.parent_id
     JOIN finan_conta c12 ON c12.id = c11.parent_id
  WHERE coalesce(c1.sintetica, False) = false

UNION ALL
 SELECT c13.id AS conta_pai_id,
    c1.id AS conta_id,
        CASE
            WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
            ELSE 1
        END AS redutora,
    13 as nivel
   FROM finan_conta c1
     JOIN finan_conta c2 ON c2.id = c1.parent_id
     JOIN finan_conta c3 ON c3.id = c2.parent_id
     JOIN finan_conta c4 ON c4.id = c3.parent_id
     JOIN finan_conta c5 ON c5.id = c4.parent_id
     JOIN finan_conta c6 ON c6.id = c5.parent_id
     JOIN finan_conta c7 ON c7.id = c6.parent_id
     JOIN finan_conta c8 ON c8.id = c7.parent_id
     JOIN finan_conta c9 ON c9.id = c8.parent_id
     JOIN finan_conta c10 ON c10.id = c9.parent_id
     JOIN finan_conta c11 ON c11.id = c10.parent_id
     JOIN finan_conta c12 ON c12.id = c11.parent_id
     JOIN finan_conta c13 ON c13.id = c12.parent_id
  WHERE coalesce(c1.sintetica, False) = false;
