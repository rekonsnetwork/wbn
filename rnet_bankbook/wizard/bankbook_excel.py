from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

import logging


_logger = logging.getLogger(__name__)


class BankbookExcel(models.TransientModel):
    _name = 'bankbook.excel'

    def print(self, data):
        _logger.info("=====")
        _logger.info(data)
        _logger.info("=====")
        raise ValidationError("It works! check the data in the log file.")
