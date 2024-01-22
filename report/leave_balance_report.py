# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################

from odoo import models, fields, tools


class LeaveBalanceReport(models.Model):
    """Balance Leave Report model"""

    _name = 'report.balance.leave'
    _description = 'Leave Balance Report'
    _auto = False

    emp_id = fields.Many2one('hr.employee', string="Employee", readonly=True)
    gender = fields.Char(string='gender', readonly=True)
    department_id = fields.Many2one('hr.department', string='Department', readonly=True)
    country_id = fields.Many2one('res.country', string='Nationality', readonly=True)
    job_id = fields.Many2one('hr.job', string='Job', readonly=True)
    leave_type_id = fields.Many2one('hr.leave.type', string='Leave Type', readonly=True)
    allocated_days = fields.Float('Allocated Balance')
    taken_days = fields.Float('Taken Leaves')
    balance_days = fields.Float('Remaining Balance')
    company_id = fields.Many2one('res.company', string="Company")
    hours_per_day = fields.Integer()

    def init(self):
        """Loads report data"""
        tools.drop_view_if_exists(self._cr, 'report_balance_leave')
        self._cr.execute(
            """
            CREATE
            OR REPLACE VIEW public.report_balance_leave(
              id,
              emp_id,
              gender,
              country_id,
              department_id,
              job_id,
              leave_type_id,
              allocated_days,
              taken_days,
              balance_days,
              company_id
            ) AS WITH hr_leave_taken_leaves(
              employee_id,
              taken_days,
              holiday_status_id
            ) AS(
              SELECT
                l_1.employee_id,
                sum(
                  CASE WHEN l_1.state :: text = 'validate' :: text THEN l_1.number_of_days ELSE 0 END
                ) AS taken_days,
                l_1.holiday_status_id
              FROM
                hr_leave l_1
              GROUP BY
                l_1.employee_id,
                l_1.holiday_status_id
            )
            SELECT
              row_number() OVER(
                ORDER BY
                  e.id
              ) AS id,
              e.id AS emp_id,
              e.gender,
              e.country_id,
              e.department_id,
              e.job_id,
              al.holiday_status_id AS leave_type_id,
              sum(al.number_of_days)::float * e.hours_per_day AS allocated_days,
              (
                SELECT
                  hr_leave_taken_leaves.taken_days
                FROM
                  hr_leave_taken_leaves
                WHERE
                  hr_leave_taken_leaves.employee_id = e.id
                  AND hr_leave_taken_leaves.holiday_status_id = al.holiday_status_id
              ) * e.hours_per_day AS taken_days,
              sum(al.number_of_days * e.hours_per_day) - COALESCE(
                (
                  SELECT
                    hr_leave_taken_leaves.taken_days * e.hours_per_day
                  FROM
                    hr_leave_taken_leaves
                  WHERE
                    hr_leave_taken_leaves.employee_id = e.id
                    AND hr_leave_taken_leaves.holiday_status_id = al.holiday_status_id
                )
              ) AS balance_days,
              e.company_id
            FROM
              hr_employee e
              JOIN hr_leave_allocation al ON al.employee_id = e.id
              AND al.state :: text = 'validate' :: text
            WHERE
              e.active = true
            GROUP BY
              e.id,
              al.holiday_status_id;

            """
        )