-- View: project_orcamento_meses_colunas

-- DROP VIEW project_orcamento_meses_colunas;

CREATE OR REPLACE VIEW project_orcamento_meses_desembolso_colunas AS 
 SELECT meses.orcamento_id,
    max(meses.mes_01) AS mes_01,
    max(meses.mes_02) AS mes_02,
    max(meses.mes_03) AS mes_03,
    max(meses.mes_04) AS mes_04,
    max(meses.mes_05) AS mes_05,
    max(meses.mes_06) AS mes_06,
    max(meses.mes_07) AS mes_07,
    max(meses.mes_08) AS mes_08,
    max(meses.mes_09) AS mes_09,
    max(meses.mes_10) AS mes_10,
    max(meses.mes_11) AS mes_11,
    max(meses.mes_12) AS mes_12,
    max(meses.mes_13) AS mes_13,
    max(meses.mes_14) AS mes_14,
    max(meses.mes_15) AS mes_15,
    max(meses.mes_16) AS mes_16,
    max(meses.mes_17) AS mes_17,
    max(meses.mes_18) AS mes_18,
    max(meses.mes_19) AS mes_19,
    max(meses.mes_20) AS mes_20,
    max(meses.mes_21) AS mes_21,
    max(meses.mes_22) AS mes_22,
    max(meses.mes_23) AS mes_23,
    max(meses.mes_24) AS mes_24
   FROM (( SELECT pom.orcamento_id,
            pom.mes AS mes_01,
            NULL::text AS mes_02,
            NULL::text AS mes_03,
            NULL::text AS mes_04,
            NULL::text AS mes_05,
            NULL::text AS mes_06,
            NULL::text AS mes_07,
            NULL::text AS mes_08,
            NULL::text AS mes_09,
            NULL::text AS mes_10,
            NULL::text AS mes_11,
            NULL::text AS mes_12,
            NULL::text AS mes_13,
            NULL::text AS mes_14,
            NULL::text AS mes_15,
            NULL::text AS mes_16,
            NULL::text AS mes_17,
            NULL::text AS mes_18,
            NULL::text AS mes_19,
            NULL::text AS mes_20,
            NULL::text AS mes_21,
            NULL::text AS mes_22,
            NULL::text AS mes_23,
            NULL::text AS mes_24
           FROM project_orcamento_meses_desembolso pom
          ORDER BY pom.mes
         LIMIT 1)
        UNION ALL
        ( SELECT pom.orcamento_id,
            NULL::text AS mes_01,
            pom.mes AS mes_02,
            NULL::text AS mes_03,
            NULL::text AS mes_04,
            NULL::text AS mes_05,
            NULL::text AS mes_06,
            NULL::text AS mes_07,
            NULL::text AS mes_08,
            NULL::text AS mes_09,
            NULL::text AS mes_10,
            NULL::text AS mes_11,
            NULL::text AS mes_12,
            NULL::text AS mes_13,
            NULL::text AS mes_14,
            NULL::text AS mes_15,
            NULL::text AS mes_16,
            NULL::text AS mes_17,
            NULL::text AS mes_18,
            NULL::text AS mes_19,
            NULL::text AS mes_20,
            NULL::text AS mes_21,
            NULL::text AS mes_22,
            NULL::text AS mes_23,
            NULL::text AS mes_24
           FROM project_orcamento_meses_desembolso pom
          ORDER BY pom.mes
         OFFSET 1
         LIMIT 1)
        UNION ALL
        ( SELECT pom.orcamento_id,
            NULL::text AS mes_01,
            NULL::text AS mes_02,
            pom.mes AS mes_03,
            NULL::text AS mes_04,
            NULL::text AS mes_05,
            NULL::text AS mes_06,
            NULL::text AS mes_07,
            NULL::text AS mes_08,
            NULL::text AS mes_09,
            NULL::text AS mes_10,
            NULL::text AS mes_11,
            NULL::text AS mes_12,
            NULL::text AS mes_13,
            NULL::text AS mes_14,
            NULL::text AS mes_15,
            NULL::text AS mes_16,
            NULL::text AS mes_17,
            NULL::text AS mes_18,
            NULL::text AS mes_19,
            NULL::text AS mes_20,
            NULL::text AS mes_21,
            NULL::text AS mes_22,
            NULL::text AS mes_23,
            NULL::text AS mes_24
           FROM project_orcamento_meses_desembolso pom
          ORDER BY pom.mes
         OFFSET 2
         LIMIT 1)
        UNION ALL
        ( SELECT pom.orcamento_id,
            NULL::text AS mes_01,
            NULL::text AS mes_02,
            NULL::text AS mes_03,
            pom.mes AS mes_04,
            NULL::text AS mes_05,
            NULL::text AS mes_06,
            NULL::text AS mes_07,
            NULL::text AS mes_08,
            NULL::text AS mes_09,
            NULL::text AS mes_10,
            NULL::text AS mes_11,
            NULL::text AS mes_12,
            NULL::text AS mes_13,
            NULL::text AS mes_14,
            NULL::text AS mes_15,
            NULL::text AS mes_16,
            NULL::text AS mes_17,
            NULL::text AS mes_18,
            NULL::text AS mes_19,
            NULL::text AS mes_20,
            NULL::text AS mes_21,
            NULL::text AS mes_22,
            NULL::text AS mes_23,
            NULL::text AS mes_24
           FROM project_orcamento_meses_desembolso pom
          ORDER BY pom.mes
         OFFSET 3
         LIMIT 1)
        UNION ALL
        ( SELECT pom.orcamento_id,
            NULL::text AS mes_01,
            NULL::text AS mes_02,
            NULL::text AS mes_03,
            NULL::text AS mes_04,
            pom.mes AS mes_05,
            NULL::text AS mes_06,
            NULL::text AS mes_07,
            NULL::text AS mes_08,
            NULL::text AS mes_09,
            NULL::text AS mes_10,
            NULL::text AS mes_11,
            NULL::text AS mes_12,
            NULL::text AS mes_13,
            NULL::text AS mes_14,
            NULL::text AS mes_15,
            NULL::text AS mes_16,
            NULL::text AS mes_17,
            NULL::text AS mes_18,
            NULL::text AS mes_19,
            NULL::text AS mes_20,
            NULL::text AS mes_21,
            NULL::text AS mes_22,
            NULL::text AS mes_23,
            NULL::text AS mes_24
           FROM project_orcamento_meses_desembolso pom
          ORDER BY pom.mes
         OFFSET 4
         LIMIT 1)
        UNION ALL
        ( SELECT pom.orcamento_id,
            NULL::text AS mes_01,
            NULL::text AS mes_02,
            NULL::text AS mes_03,
            NULL::text AS mes_04,
            NULL::text AS mes_05,
            pom.mes AS mes_06,
            NULL::text AS mes_07,
            NULL::text AS mes_08,
            NULL::text AS mes_09,
            NULL::text AS mes_10,
            NULL::text AS mes_11,
            NULL::text AS mes_12,
            NULL::text AS mes_13,
            NULL::text AS mes_14,
            NULL::text AS mes_15,
            NULL::text AS mes_16,
            NULL::text AS mes_17,
            NULL::text AS mes_18,
            NULL::text AS mes_19,
            NULL::text AS mes_20,
            NULL::text AS mes_21,
            NULL::text AS mes_22,
            NULL::text AS mes_23,
            NULL::text AS mes_24
           FROM project_orcamento_meses_desembolso pom
          ORDER BY pom.mes
         OFFSET 5
         LIMIT 1)
        UNION ALL
        ( SELECT pom.orcamento_id,
            NULL::text AS mes_01,
            NULL::text AS mes_02,
            NULL::text AS mes_03,
            NULL::text AS mes_04,
            NULL::text AS mes_05,
            NULL::text AS mes_06,
            pom.mes AS mes_07,
            NULL::text AS mes_08,
            NULL::text AS mes_09,
            NULL::text AS mes_10,
            NULL::text AS mes_11,
            NULL::text AS mes_12,
            NULL::text AS mes_13,
            NULL::text AS mes_14,
            NULL::text AS mes_15,
            NULL::text AS mes_16,
            NULL::text AS mes_17,
            NULL::text AS mes_18,
            NULL::text AS mes_19,
            NULL::text AS mes_20,
            NULL::text AS mes_21,
            NULL::text AS mes_22,
            NULL::text AS mes_23,
            NULL::text AS mes_24
           FROM project_orcamento_meses_desembolso pom
          ORDER BY pom.mes
         OFFSET 6
         LIMIT 1)
        UNION ALL
        ( SELECT pom.orcamento_id,
            NULL::text AS mes_01,
            NULL::text AS mes_02,
            NULL::text AS mes_03,
            NULL::text AS mes_04,
            NULL::text AS mes_05,
            NULL::text AS mes_06,
            NULL::text AS mes_07,
            pom.mes AS mes_08,
            NULL::text AS mes_09,
            NULL::text AS mes_10,
            NULL::text AS mes_11,
            NULL::text AS mes_12,
            NULL::text AS mes_13,
            NULL::text AS mes_14,
            NULL::text AS mes_15,
            NULL::text AS mes_16,
            NULL::text AS mes_17,
            NULL::text AS mes_18,
            NULL::text AS mes_19,
            NULL::text AS mes_20,
            NULL::text AS mes_21,
            NULL::text AS mes_22,
            NULL::text AS mes_23,
            NULL::text AS mes_24
           FROM project_orcamento_meses_desembolso pom
          ORDER BY pom.mes
         OFFSET 7
         LIMIT 1)
        UNION ALL
        ( SELECT pom.orcamento_id,
            NULL::text AS mes_01,
            NULL::text AS mes_02,
            NULL::text AS mes_03,
            NULL::text AS mes_04,
            NULL::text AS mes_05,
            NULL::text AS mes_06,
            NULL::text AS mes_07,
            NULL::text AS mes_08,
            pom.mes AS mes_09,
            NULL::text AS mes_10,
            NULL::text AS mes_11,
            NULL::text AS mes_12,
            NULL::text AS mes_13,
            NULL::text AS mes_14,
            NULL::text AS mes_15,
            NULL::text AS mes_16,
            NULL::text AS mes_17,
            NULL::text AS mes_18,
            NULL::text AS mes_19,
            NULL::text AS mes_20,
            NULL::text AS mes_21,
            NULL::text AS mes_22,
            NULL::text AS mes_23,
            NULL::text AS mes_24
           FROM project_orcamento_meses_desembolso pom
          ORDER BY pom.mes
         OFFSET 8
         LIMIT 1)
        UNION ALL
        ( SELECT pom.orcamento_id,
            NULL::text AS mes_01,
            NULL::text AS mes_02,
            NULL::text AS mes_03,
            NULL::text AS mes_04,
            NULL::text AS mes_05,
            NULL::text AS mes_06,
            NULL::text AS mes_07,
            NULL::text AS mes_08,
            NULL::text AS mes_09,
            pom.mes AS mes_10,
            NULL::text AS mes_11,
            NULL::text AS mes_12,
            NULL::text AS mes_13,
            NULL::text AS mes_14,
            NULL::text AS mes_15,
            NULL::text AS mes_16,
            NULL::text AS mes_17,
            NULL::text AS mes_18,
            NULL::text AS mes_19,
            NULL::text AS mes_20,
            NULL::text AS mes_21,
            NULL::text AS mes_22,
            NULL::text AS mes_23,
            NULL::text AS mes_24
           FROM project_orcamento_meses_desembolso pom
          ORDER BY pom.mes
         OFFSET 9
         LIMIT 1)
        UNION ALL
        ( SELECT pom.orcamento_id,
            NULL::text AS mes_01,
            NULL::text AS mes_02,
            NULL::text AS mes_03,
            NULL::text AS mes_04,
            NULL::text AS mes_05,
            NULL::text AS mes_06,
            NULL::text AS mes_07,
            NULL::text AS mes_08,
            NULL::text AS mes_09,
            NULL::text AS mes_10,
            pom.mes AS mes_11,
            NULL::text AS mes_12,
            NULL::text AS mes_13,
            NULL::text AS mes_14,
            NULL::text AS mes_15,
            NULL::text AS mes_16,
            NULL::text AS mes_17,
            NULL::text AS mes_18,
            NULL::text AS mes_19,
            NULL::text AS mes_20,
            NULL::text AS mes_21,
            NULL::text AS mes_22,
            NULL::text AS mes_23,
            NULL::text AS mes_24
           FROM project_orcamento_meses_desembolso pom
          ORDER BY pom.mes
         OFFSET 10
         LIMIT 1)
        UNION ALL
        ( SELECT pom.orcamento_id,
            NULL::text AS mes_01,
            NULL::text AS mes_02,
            NULL::text AS mes_03,
            NULL::text AS mes_04,
            NULL::text AS mes_05,
            NULL::text AS mes_06,
            NULL::text AS mes_07,
            NULL::text AS mes_08,
            NULL::text AS mes_09,
            NULL::text AS mes_10,
            NULL::text AS mes_11,
            pom.mes AS mes_12,
            NULL::text AS mes_13,
            NULL::text AS mes_14,
            NULL::text AS mes_15,
            NULL::text AS mes_16,
            NULL::text AS mes_17,
            NULL::text AS mes_18,
            NULL::text AS mes_19,
            NULL::text AS mes_20,
            NULL::text AS mes_21,
            NULL::text AS mes_22,
            NULL::text AS mes_23,
            NULL::text AS mes_24
           FROM project_orcamento_meses_desembolso pom
          ORDER BY pom.mes
         OFFSET 11
         LIMIT 1)
        UNION ALL
        ( SELECT pom.orcamento_id,
            NULL::text AS mes_01,
            NULL::text AS mes_02,
            NULL::text AS mes_03,
            NULL::text AS mes_04,
            NULL::text AS mes_05,
            NULL::text AS mes_06,
            NULL::text AS mes_07,
            NULL::text AS mes_08,
            NULL::text AS mes_09,
            NULL::text AS mes_10,
            NULL::text AS mes_11,
            NULL::text AS mes_12,
            pom.mes AS mes_13,
            NULL::text AS mes_14,
            NULL::text AS mes_15,
            NULL::text AS mes_16,
            NULL::text AS mes_17,
            NULL::text AS mes_18,
            NULL::text AS mes_19,
            NULL::text AS mes_20,
            NULL::text AS mes_21,
            NULL::text AS mes_22,
            NULL::text AS mes_23,
            NULL::text AS mes_24
           FROM project_orcamento_meses_desembolso pom
          ORDER BY pom.mes
         OFFSET 12
         LIMIT 1)
        UNION ALL
        ( SELECT pom.orcamento_id,
            NULL::text AS mes_01,
            NULL::text AS mes_02,
            NULL::text AS mes_03,
            NULL::text AS mes_04,
            NULL::text AS mes_05,
            NULL::text AS mes_06,
            NULL::text AS mes_07,
            NULL::text AS mes_08,
            NULL::text AS mes_09,
            NULL::text AS mes_10,
            NULL::text AS mes_11,
            NULL::text AS mes_12,
            NULL::text AS mes_13,
            pom.mes AS mes_14,
            NULL::text AS mes_15,
            NULL::text AS mes_16,
            NULL::text AS mes_17,
            NULL::text AS mes_18,
            NULL::text AS mes_19,
            NULL::text AS mes_20,
            NULL::text AS mes_21,
            NULL::text AS mes_22,
            NULL::text AS mes_23,
            NULL::text AS mes_24
           FROM project_orcamento_meses_desembolso pom
          ORDER BY pom.mes
         OFFSET 13
         LIMIT 1)
        UNION ALL
        ( SELECT pom.orcamento_id,
            NULL::text AS mes_01,
            NULL::text AS mes_02,
            NULL::text AS mes_03,
            NULL::text AS mes_04,
            NULL::text AS mes_05,
            NULL::text AS mes_06,
            NULL::text AS mes_07,
            NULL::text AS mes_08,
            NULL::text AS mes_09,
            NULL::text AS mes_10,
            NULL::text AS mes_11,
            NULL::text AS mes_12,
            NULL::text AS mes_13,
            NULL::text AS mes_14,
            pom.mes AS mes_15,
            NULL::text AS mes_16,
            NULL::text AS mes_17,
            NULL::text AS mes_18,
            NULL::text AS mes_19,
            NULL::text AS mes_20,
            NULL::text AS mes_21,
            NULL::text AS mes_22,
            NULL::text AS mes_23,
            NULL::text AS mes_24
           FROM project_orcamento_meses_desembolso pom
          ORDER BY pom.mes
         OFFSET 14
         LIMIT 1)
        UNION ALL
        ( SELECT pom.orcamento_id,
            NULL::text AS mes_01,
            NULL::text AS mes_02,
            NULL::text AS mes_03,
            NULL::text AS mes_04,
            NULL::text AS mes_05,
            NULL::text AS mes_06,
            NULL::text AS mes_07,
            NULL::text AS mes_08,
            NULL::text AS mes_09,
            NULL::text AS mes_10,
            NULL::text AS mes_11,
            NULL::text AS mes_12,
            NULL::text AS mes_13,
            NULL::text AS mes_14,
            NULL::text AS mes_15,
            pom.mes AS mes_16,
            NULL::text AS mes_17,
            NULL::text AS mes_18,
            NULL::text AS mes_19,
            NULL::text AS mes_20,
            NULL::text AS mes_21,
            NULL::text AS mes_22,
            NULL::text AS mes_23,
            NULL::text AS mes_24
           FROM project_orcamento_meses_desembolso pom
          ORDER BY pom.mes
         OFFSET 15
         LIMIT 1)
        UNION ALL
        ( SELECT pom.orcamento_id,
            NULL::text AS mes_01,
            NULL::text AS mes_02,
            NULL::text AS mes_03,
            NULL::text AS mes_04,
            NULL::text AS mes_05,
            NULL::text AS mes_06,
            NULL::text AS mes_07,
            NULL::text AS mes_08,
            NULL::text AS mes_09,
            NULL::text AS mes_10,
            NULL::text AS mes_11,
            NULL::text AS mes_12,
            NULL::text AS mes_13,
            NULL::text AS mes_14,
            NULL::text AS mes_15,
            NULL::text AS mes_16,
            pom.mes AS mes_17,
            NULL::text AS mes_18,
            NULL::text AS mes_19,
            NULL::text AS mes_20,
            NULL::text AS mes_21,
            NULL::text AS mes_22,
            NULL::text AS mes_23,
            NULL::text AS mes_24
           FROM project_orcamento_meses_desembolso pom
          ORDER BY pom.mes
         OFFSET 16
         LIMIT 1)
        UNION ALL
        ( SELECT pom.orcamento_id,
            NULL::text AS mes_01,
            NULL::text AS mes_02,
            NULL::text AS mes_03,
            NULL::text AS mes_04,
            NULL::text AS mes_05,
            NULL::text AS mes_06,
            NULL::text AS mes_07,
            NULL::text AS mes_08,
            NULL::text AS mes_09,
            NULL::text AS mes_10,
            NULL::text AS mes_11,
            NULL::text AS mes_12,
            NULL::text AS mes_13,
            NULL::text AS mes_14,
            NULL::text AS mes_15,
            NULL::text AS mes_16,
            NULL::text AS mes_17,
            pom.mes AS mes_18,
            NULL::text AS mes_19,
            NULL::text AS mes_20,
            NULL::text AS mes_21,
            NULL::text AS mes_22,
            NULL::text AS mes_23,
            NULL::text AS mes_24
           FROM project_orcamento_meses_desembolso pom
          ORDER BY pom.mes
         OFFSET 17
         LIMIT 1)
        UNION ALL
        ( SELECT pom.orcamento_id,
            NULL::text AS mes_01,
            NULL::text AS mes_02,
            NULL::text AS mes_03,
            NULL::text AS mes_04,
            NULL::text AS mes_05,
            NULL::text AS mes_06,
            NULL::text AS mes_07,
            NULL::text AS mes_08,
            NULL::text AS mes_09,
            NULL::text AS mes_10,
            NULL::text AS mes_11,
            NULL::text AS mes_12,
            NULL::text AS mes_13,
            NULL::text AS mes_14,
            NULL::text AS mes_15,
            NULL::text AS mes_16,
            NULL::text AS mes_17,
            NULL::text AS mes_18,
            pom.mes AS mes_19,
            NULL::text AS mes_20,
            NULL::text AS mes_21,
            NULL::text AS mes_22,
            NULL::text AS mes_23,
            NULL::text AS mes_24
           FROM project_orcamento_meses_desembolso pom
          ORDER BY pom.mes
         OFFSET 18
         LIMIT 1)
        UNION ALL
        ( SELECT pom.orcamento_id,
            NULL::text AS mes_01,
            NULL::text AS mes_02,
            NULL::text AS mes_03,
            NULL::text AS mes_04,
            NULL::text AS mes_05,
            NULL::text AS mes_06,
            NULL::text AS mes_07,
            NULL::text AS mes_08,
            NULL::text AS mes_09,
            NULL::text AS mes_10,
            NULL::text AS mes_11,
            NULL::text AS mes_12,
            NULL::text AS mes_13,
            NULL::text AS mes_14,
            NULL::text AS mes_15,
            NULL::text AS mes_16,
            NULL::text AS mes_17,
            NULL::text AS mes_18,
            NULL::text AS mes_19,
            pom.mes AS mes_20,
            NULL::text AS mes_21,
            NULL::text AS mes_22,
            NULL::text AS mes_23,
            NULL::text AS mes_24
           FROM project_orcamento_meses_desembolso pom
          ORDER BY pom.mes
         OFFSET 19
         LIMIT 1)
        UNION ALL
        ( SELECT pom.orcamento_id,
            NULL::text AS mes_01,
            NULL::text AS mes_02,
            NULL::text AS mes_03,
            NULL::text AS mes_04,
            NULL::text AS mes_05,
            NULL::text AS mes_06,
            NULL::text AS mes_07,
            NULL::text AS mes_08,
            NULL::text AS mes_09,
            NULL::text AS mes_10,
            NULL::text AS mes_11,
            NULL::text AS mes_12,
            NULL::text AS mes_13,
            NULL::text AS mes_14,
            NULL::text AS mes_15,
            NULL::text AS mes_16,
            NULL::text AS mes_17,
            NULL::text AS mes_18,
            NULL::text AS mes_19,
            NULL::text AS mes_20,
            pom.mes AS mes_21,
            NULL::text AS mes_22,
            NULL::text AS mes_23,
            NULL::text AS mes_24
           FROM project_orcamento_meses_desembolso pom
          ORDER BY pom.mes
         OFFSET 20
         LIMIT 1)
        UNION ALL
        ( SELECT pom.orcamento_id,
            NULL::text AS mes_01,
            NULL::text AS mes_02,
            NULL::text AS mes_03,
            NULL::text AS mes_04,
            NULL::text AS mes_05,
            NULL::text AS mes_06,
            NULL::text AS mes_07,
            NULL::text AS mes_08,
            NULL::text AS mes_09,
            NULL::text AS mes_10,
            NULL::text AS mes_11,
            NULL::text AS mes_12,
            NULL::text AS mes_13,
            NULL::text AS mes_14,
            NULL::text AS mes_15,
            NULL::text AS mes_16,
            NULL::text AS mes_17,
            NULL::text AS mes_18,
            NULL::text AS mes_19,
            NULL::text AS mes_20,
            NULL::text AS mes_21,
            pom.mes AS mes_22,
            NULL::text AS mes_23,
            NULL::text AS mes_24
           FROM project_orcamento_meses_desembolso pom
          ORDER BY pom.mes
         OFFSET 21
         LIMIT 1)
        UNION ALL
        ( SELECT pom.orcamento_id,
            NULL::text AS mes_01,
            NULL::text AS mes_02,
            NULL::text AS mes_03,
            NULL::text AS mes_04,
            NULL::text AS mes_05,
            NULL::text AS mes_06,
            NULL::text AS mes_07,
            NULL::text AS mes_08,
            NULL::text AS mes_09,
            NULL::text AS mes_10,
            NULL::text AS mes_11,
            NULL::text AS mes_12,
            NULL::text AS mes_13,
            NULL::text AS mes_14,
            NULL::text AS mes_15,
            NULL::text AS mes_16,
            NULL::text AS mes_17,
            NULL::text AS mes_18,
            NULL::text AS mes_19,
            NULL::text AS mes_20,
            NULL::text AS mes_21,
            NULL::text AS mes_22,
            pom.mes AS mes_23,
            NULL::text AS mes_24
           FROM project_orcamento_meses_desembolso pom
          ORDER BY pom.mes
         OFFSET 22
         LIMIT 1)
        UNION ALL
        ( SELECT pom.orcamento_id,
            NULL::text AS mes_01,
            NULL::text AS mes_02,
            NULL::text AS mes_03,
            NULL::text AS mes_04,
            NULL::text AS mes_05,
            NULL::text AS mes_06,
            NULL::text AS mes_07,
            NULL::text AS mes_08,
            NULL::text AS mes_09,
            NULL::text AS mes_10,
            NULL::text AS mes_11,
            NULL::text AS mes_12,
            NULL::text AS mes_13,
            NULL::text AS mes_14,
            NULL::text AS mes_15,
            NULL::text AS mes_16,
            NULL::text AS mes_17,
            NULL::text AS mes_18,
            NULL::text AS mes_19,
            NULL::text AS mes_20,
            NULL::text AS mes_21,
            NULL::text AS mes_22,
            NULL::text AS mes_23,
            pom.mes AS mes_24
           FROM project_orcamento_meses_desembolso pom
          ORDER BY pom.mes
         OFFSET 23
         LIMIT 1)) meses
  GROUP BY meses.orcamento_id;

