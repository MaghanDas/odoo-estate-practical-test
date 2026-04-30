# estate_account/tests/test_estate_account.py

from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


class TestEstateAccount(TransactionCase):
    """
    Automated tests for the estate_account module.
    Mirrors the acceptance-criteria pseudocode provided in the task brief.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # A real contact to act as buyer
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Buyer',
            'email': 'buyer@test.com',
        })

        # A property ready to receive offers
        cls.property = cls.env['estate.property'].create({
            'name': 'Test Villa',
            'expected_price': 200000.00,
            'postcode': '1000',
        })

    # ------------------------------------------------------------------
    # Core acceptance-criteria test (mirrors evaluator pseudocode exactly)
    # ------------------------------------------------------------------

    def test_action_sold_creates_invoice(self):
        """
        Acceptance criteria from task brief:
            property.invoice_count == 1
            inv.move_type == 'out_invoice'
            inv.partner_id == partner
            inv.amount_untaxed == 200000 * 0.06 + 100
            inv.state == 'draft'
        """
        offer = self.env['estate.property.offer'].create({
            'property_id': self.property.id,
            'price': 200000.00,
            'partner_id': self.partner.id,
        })

        offer.action_accept()
        self.property.action_sold()

        # Invoice count
        self.assertEqual(self.property.invoice_count, 1)

        inv = self.property.invoice_ids
        self.assertEqual(len(inv), 1)

        # Invoice type
        self.assertEqual(inv.move_type, 'out_invoice')

        # Partner matches buyer
        self.assertEqual(inv.partner_id, self.partner)

        # Untaxed amount: 6% commission + 100 admin fee
        expected_amount = 200000.00 * 0.06 + 100.00   # = 12100.00
        self.assertAlmostEqual(inv.amount_untaxed, expected_amount, places=2)

        # Invoice is draft (not posted)
        self.assertEqual(inv.state, 'draft')

    # ------------------------------------------------------------------
    # Guard: cannot sell without a buyer
    # ------------------------------------------------------------------

    def test_action_sold_without_buyer_raises(self):
        """Selling without an accepted offer (no buyer_id) must fail gracefully."""
        prop = self.env['estate.property'].create({
            'name': 'No Buyer Property',
            'expected_price': 150000.00,
        })

        with self.assertRaises(UserError):
            prop.action_sold()

    # ------------------------------------------------------------------
    # Idempotency: selling twice must not create two invoices
    # ------------------------------------------------------------------

    def test_action_sold_twice_raises(self):
        """Re-running action_sold on an already-sold property must raise UserError."""
        prop = self.env['estate.property'].create({
            'name': 'Double Sold Property',
            'expected_price': 100000.00,
        })

        offer = self.env['estate.property.offer'].create({
            'property_id': prop.id,
            'price': 100000.00,
            'partner_id': self.partner.id,
        })
        offer.action_accept()
        prop.action_sold()

        # Second call must raise, not silently create a duplicate invoice
        with self.assertRaises(UserError):
            prop.action_sold()

        # Confirm only one invoice exists
        self.assertEqual(prop.invoice_count, 1)

    # ------------------------------------------------------------------
    # Invoice line breakdown
    # ------------------------------------------------------------------

    def test_invoice_line_details(self):
        """Invoice must have exactly two lines: commission and admin fee."""
        prop = self.env['estate.property'].create({
            'name': 'Line Detail Property',
            'expected_price': 300000.00,
        })

        offer = self.env['estate.property.offer'].create({
            'property_id': prop.id,
            'price': 300000.00,
            'partner_id': self.partner.id,
        })
        offer.action_accept()
        prop.action_sold()

        inv = prop.invoice_ids
        lines = inv.invoice_line_ids

        self.assertEqual(len(lines), 2)

        commission_line = lines.filtered(lambda l: 'Commission' in l.name)
        admin_line = lines.filtered(lambda l: 'Administrative' in l.name)

        self.assertTrue(commission_line, "Commission line not found")
        self.assertTrue(admin_line, "Admin fee line not found")

        self.assertAlmostEqual(commission_line.price_unit, 300000.00 * 0.06, places=2)
        self.assertAlmostEqual(admin_line.price_unit, 100.00, places=2)
