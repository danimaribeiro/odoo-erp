update project_project p set name = (select a.name from account_analytic_account a where a.id = p.analytic_account_id);
update project_project p set partner_id = (select a.partner_id from account_analytic_account a where a.id = p.analytic_account_id);
update project_project p set user_id = (select a.user_id from account_analytic_account a where a.id = p.analytic_account_id);
update project_project p set parent_id = (select a.parent_id from account_analytic_account a where a.id = p.analytic_account_id);