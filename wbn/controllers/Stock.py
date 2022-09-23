import re

from odoo import http, _
from odoo.http import request, Controller, content_disposition
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)


class Portal(Controller):

    @http.route(['/picking/preview/<int:picking_id>'])
    def preview_picking(self, picking_id, access_token='', report_type=None, download=False):
        picking = request.env['stock.picking'].browse([picking_id])

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=picking, report_type=report_type, report_ref='stock.action_report_delivery', download=download)
        values = {'picking': picking}
        return request.render('wbn.preview_picking', values)

    def _show_report(self, model, report_type, report_ref, download=False):
        if report_type not in ('html', 'pdf', 'text'):
            raise UserError(_("Invalid report type: %s") % report_type)

        report_sudo = request.env.ref(report_ref).sudo()

        if not isinstance(report_sudo, type(request.env['ir.actions.report'])):
            raise UserError(_("%s is not the reference of a report") % report_ref)

        method_name = 'render_qweb_%s' % (report_type)
        report = getattr(report_sudo, method_name)([model.id], data={'report_type': report_type})[0]
        reporthttpheaders = [
            ('Content-Type', 'application/pdf' if report_type == 'pdf' else 'text/html'),
            ('Content-Length', len(report)),
        ]
        if report_type == 'pdf' and download:
            filename = "%s.pdf" % (re.sub('\W+', '-', model._get_report_base_filename()))
            reporthttpheaders.append(('Content-Disposition', content_disposition(filename)))
        return request.make_response(report, headers=reporthttpheaders)

