sql = """
DROP VIEW econo_conta_arvore;

CREATE OR REPLACE VIEW econo_conta_arvore AS
 SELECT c1.id,
    c1.id AS conta_id,
        CASE
            WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
            ELSE 1
        END AS redutora
   FROM econo_conta c1
  WHERE c1.sintetica = false
UNION ALL
 SELECT c2.id,
    c1.id AS conta_id,
        CASE
            WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
            ELSE 1
        END AS redutora
   FROM econo_conta c1
     JOIN econo_conta c2 ON c2.id = c1.parent_id
  WHERE c1.sintetica = false
UNION ALL
 SELECT c3.id,
    c1.id AS conta_id,
        CASE
            WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
            ELSE 1
        END AS redutora
   FROM econo_conta c1
     JOIN econo_conta c2 ON c2.id = c1.parent_id
     JOIN econo_conta c3 ON c3.id = c2.parent_id
  WHERE c1.sintetica = false
UNION ALL
 SELECT c4.id,
    c1.id AS conta_id,
        CASE
            WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
            ELSE 1
        END AS redutora
   FROM econo_conta c1
     JOIN econo_conta c2 ON c2.id = c1.parent_id
     JOIN econo_conta c3 ON c3.id = c2.parent_id
     JOIN econo_conta c4 ON c4.id = c3.parent_id
  WHERE c1.sintetica = false
UNION ALL
 SELECT c5.id,
    c1.id AS conta_id,
        CASE
            WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
            ELSE 1
        END AS redutora
   FROM econo_conta c1
     JOIN econo_conta c2 ON c2.id = c1.parent_id
     JOIN econo_conta c3 ON c3.id = c2.parent_id
     JOIN econo_conta c4 ON c4.id = c3.parent_id
     JOIN econo_conta c5 ON c5.id = c4.parent_id
  WHERE c1.sintetica = false
UNION ALL
 SELECT c6.id,
    c1.id AS conta_id,
        CASE
            WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
            ELSE 1
        END AS redutora
   FROM econo_conta c1
     JOIN econo_conta c2 ON c2.id = c1.parent_id
     JOIN econo_conta c3 ON c3.id = c2.parent_id
     JOIN econo_conta c4 ON c4.id = c3.parent_id
     JOIN econo_conta c5 ON c5.id = c4.parent_id
     JOIN econo_conta c6 ON c6.id = c5.parent_id
  WHERE c1.sintetica = false
UNION ALL
 SELECT c7.id,
    c1.id AS conta_id,
        CASE
            WHEN "left"(c1.nome::text, 3) = '(-)'::text THEN (-1)
            ELSE 1
        END AS redutora
   FROM econo_conta c1
     JOIN econo_conta c2 ON c2.id = c1.parent_id
     JOIN econo_conta c3 ON c3.id = c2.parent_id
     JOIN econo_conta c4 ON c4.id = c3.parent_id
     JOIN econo_conta c5 ON c5.id = c4.parent_id
     JOIN econo_conta c6 ON c6.id = c5.parent_id
     JOIN econo_conta c7 ON c7.id = c6.parent_id
  WHERE c1.sintetica = false;

"""