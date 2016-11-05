SELECT
     product_template."name" AS product_template_name,
     product_template."standard_price" AS product_template_standard_price,
     product_product."product_image_small" AS product_product_product_image_small,
     product_product."color" AS product_product_color,
     product_product."price_extra" AS product_product_price_extra,
     product_category."name" AS product_category_name,
     product_template."categ_id" AS product_template_categ_id,
     product_template."id" AS product_template_id,
     product_product."product_tmpl_id" AS product_product_product_tmpl_id,
     product_category."id" AS product_category_id
FROM
     "public"."product_template" product_template INNER JOIN "public"."product_product" product_product ON product_template."id" = product_product."product_tmpl_id"
     INNER JOIN "public"."product_category" product_category ON product_template."categ_id" = product_category."id"