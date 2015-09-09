from __future__ import division
import unittest
import numpy as np
import pyqtgraph as pg
from pyinduct import core as cr, simulation as sim, utils as ut, visualization as vis, trajectory as tr

__author__ = 'Stefan Ecklebe'

# show_plots = False
show_plots = True
# TODO Test for all Placeholders


class FieldVariableTest(unittest.TestCase):

    def setUp(self):
        nodes, self.ini_funcs = ut.cure_interval(cr.LagrangeFirstOrder, (0, 1), node_count=2)

    def test_FieldVariable(self):
        # Factor (Base)
        self.assertRaises(TypeError, sim.FieldVariable, self.ini_funcs, [0, 0])  # list instead of tuple
        self.assertRaises(ValueError, sim.FieldVariable, self.ini_funcs, (3, 0))  # order too high
        self.assertRaises(ValueError, sim.FieldVariable, self.ini_funcs, (0, 3))  # order too high
        self.assertRaises(ValueError, sim.FieldVariable, self.ini_funcs, (2, 2))  # order too high
        self.assertRaises(ValueError, sim.FieldVariable, self.ini_funcs, (-1, 3))  # order negative
        a = sim.FieldVariable(self.ini_funcs, (0, 0), 7)
        self.assertEqual((0, 0), a.order)
        self.assertEqual(7, a.location)

    def test_TemporalDerivativeFactor(self):
        # TODO
        pass
        # # TemporalDerivativeFactor
        # self.assertRaises(TypeError, sim.TemporalDerivativeFactor, "high order", "about five")
        # self.assertRaises(ValueError, sim.TemporalDerivativeFactor, 3, 7)
        # a = sim.TemporalDerivativeFactor(2, 7)
        # self.assertEqual("temporal", a.kind)
        # self.assertEqual(2, a.order)
        # self.assertEqual(7, a.factor)
        # self.assertEqual(None, a.location)
        #
        # # SpatialDerivativeFactor
        # self.assertRaises(TypeError, sim.SpatialDerivativeFactor, "high order", "about five")
        # self.assertRaises(ValueError, sim.SpatialDerivativeFactor, 3, 7)
        # a = sim.SpatialDerivativeFactor(2, 7)
        # self.assertEqual("spatial", a.kind)
        # self.assertEqual(2, a.order)
        # self.assertEqual(7, a.factor)
        # self.assertEqual(None, a.location)
        #
        # # MixedDerivativeFactor
        # self.assertRaises(TypeError, sim.MixedDerivativeFactor, "about five")
        # a = sim.MixedDerivativeFactor(7)
        # self.assertEqual("spatial/temporal", a.kind)
        # self.assertEqual(1, a.order)
        # self.assertEqual(7, a.factor)
        # self.assertEqual(None, a.location)


class ProductTest(unittest.TestCase):

    def scale(self, z):
            return 2

    def a2(self, z):
            return 5*z

    def setUp(self):
        self.input = sim.Input(np.sin)
        self.phi = cr.Function(np.sin)
        self.psi = cr.Function(np.sin)
        self.funcs = sim.TestFunctions(np.array([self.phi, self.psi]))
        self.scale_funcs = sim.ScalarFunctions(np.array([cr.Function(self.scale), cr.Function(self.scale)]))
        nodes, self.ini_funcs = ut.cure_interval(cr.LagrangeFirstOrder, (0, 1), node_count=2)
        self.field_var = sim.FieldVariable(self.ini_funcs)

    def test_product(self):
        self.assertRaises(TypeError, sim.Product, cr.Function, cr.Function)  # only Placeholders allowed
        p1 = sim.Product(self.input, self.funcs)
        p2 = sim.Product(self.funcs, self.field_var)

        # test single argument call
        p3 = sim.Product(self.funcs)
        self.assertAlmostEqual(p3.args[0].data[0](np.pi/2), 1)
        self.assertTrue(p3.b_empty)

        # test automated evaluation of Product with Scaled function
        p4 = sim.Product(self.field_var, self.scale_funcs)
        self.assertTrue(isinstance(p4.args[0], sim.FieldVariable))
        self.assertEqual(p4.args[0].data[0](0), self.scale(0)*self.ini_funcs[0](0))
        self.assertEqual(p4.args[0].data[1](1), self.scale(1)*self.ini_funcs[1](1))
        self.assertEqual(p4.args[1], None)
        self.assertTrue(p4.b_empty)

        # test automated simplification of cascaded products
        p5 = sim.Product(sim.Product(self.field_var, self.scale_funcs),
                         sim.Product(self.funcs, self.scale_funcs))
        self.assertEqual(p5.args[0].data[0](0), self.scale(0)*self.ini_funcs[0](0))
        self.assertEqual(p5.args[0].data[1](1), self.scale(1)*self.ini_funcs[1](1))
        self.assertEqual(p5.args[1].data[0](0), self.scale(0)*self.phi(0))
        self.assertEqual(p5.args[1].data[1](1), self.scale(1)*self.psi(1))
        self.assertFalse(p5.b_empty)

        # test methods
        self.assertEqual(p1.get_arg_by_class(sim.Input), [self.input])
        self.assertEqual(p1.get_arg_by_class(sim.TestFunctions), [self.funcs])
        self.assertEqual(p2.get_arg_by_class(sim.TestFunctions), [self.funcs])
        self.assertEqual(p2.get_arg_by_class(sim.FieldVariable), [self.field_var])


class WeakTermsTest(unittest.TestCase):

    def setUp(self):
        self.input = sim.Input(np.sin)
        self.phi = cr.Function(lambda x: 2*x)
        self.test_func = sim.TestFunctions(self.phi)
        nodes, self.ini_funcs = ut.cure_interval(cr.LagrangeFirstOrder, (0, 1), node_count=2)
        self.xdt = sim.TemporalDerivedFieldVariable(self.ini_funcs, 1)
        self.xdz_at1 = sim.SpatialDerivedFieldVariable(self.ini_funcs, 1, 1)
        self.prod = sim.Product(self.input, self.xdt)

    def test_WeakEquationTerm(self):
        self.assertRaises(TypeError, sim.EquationTerm, "eleven", self.input)  # scale is not a number
        self.assertRaises(TypeError, sim.EquationTerm, 1, cr.LagrangeFirstOrder(0, 1, 2))  # arg is invalid
        sim.EquationTerm(1, self.test_func)
        sim.EquationTerm(1, self.xdt)
        t1 = sim.EquationTerm(1, self.input)
        self.assertEqual(t1.scale, 1)
        self.assertEqual(t1.arg.args[0], self.input)  # automatically create Product object if only one arg is provided

    def test_ScalarTerm(self):
        self.assertRaises(TypeError, sim.ScalarTerm, 7)  # factor is number
        self.assertRaises(TypeError, sim.ScalarTerm, cr.Function(np.sin))  # factor is Function
        sim.ScalarTerm(self.input)
        self.assertRaises(ValueError, sim.ScalarTerm, self.test_func)  # integration has to be done
        t1 = sim.ScalarTerm(self.xdz_at1)
        self.assertEqual(t1.scale, 1.0)  # default scale
        # check if automated evaluation works
        self.assertTrue(np.allclose(t1.arg.args[0].data, np.array([0,  1])))

    def test_IntegralTerm(self):
        self.assertRaises(TypeError, sim.IntegralTerm, 7, (0, 1))  # integrand is number
        self.assertRaises(TypeError, sim.IntegralTerm, cr.Function(np.sin), (0, 1))  # integrand is Function
        self.assertRaises(ValueError, sim.IntegralTerm, self.xdz_at1, (0, 1))  # nothing left after evaluation
        self.assertRaises(TypeError, sim.IntegralTerm, self.xdt, [0, 1])  # limits is list

        sim.IntegralTerm(self.test_func, (0, 1))  # integrand is Placeholder
        self.assertRaises(ValueError, sim.IntegralTerm, self.input, (0, 1))  # nothing to do
        sim.IntegralTerm(self.xdt, (0, 1))  # integrand is Placeholder
        sim.IntegralTerm(self.prod, (0, 1))  # integrand is Product

        t1 = sim.IntegralTerm(self.xdt, (0, 1))
        self.assertEqual(t1.scale, 1.0)  # default scale
        self.assertEqual(t1.arg.args[0], self.xdt)  # automated product creation
        self.assertEqual(t1.limits, (0, 1))


class WeakFormulationTest(unittest.TestCase):

    def setUp(self):
        self.u = np.sin
        self.input = sim.Input(self.u)  # control input
        nodes, self.ini_funcs = ut.cure_interval(cr.LagrangeFirstOrder, (0, 1), node_count=3)
        self.phi = sim.TestFunctions(self.ini_funcs)  # eigenfunction or something else
        self.dphi = sim.TestFunctions(self.ini_funcs, order=1)  # eigenfunction or something else
        self.dphi_at1 = sim.TestFunctions(self.ini_funcs, order=1, location=1)  # eigenfunction or something else
        self.field_var = sim.FieldVariable(self.ini_funcs)
        self.field_var_at1 = sim.FieldVariable(self.ini_funcs, location=1)

    def test_init(self):
        self.assertRaises(TypeError, sim.WeakFormulation, ["a", "b"])
        sim.WeakFormulation(sim.ScalarTerm(self.field_var_at1))  # scalar case
        sim.WeakFormulation([sim.ScalarTerm(self.field_var_at1),
                             sim.IntegralTerm(self.field_var, (0, 1))
                             ])  # vector case


class CanonicalFormTest(unittest.TestCase):

    def setUp(self):
        self.cf = sim.CanonicalForm()

    def test_add_to(self):
        a = np.eye(5)
        self.cf.add_to(("E", 0), a)
        self.assertTrue(np.array_equal(self.cf._E0, a))
        self.cf.add_to(("E", 0), 5*a)
        self.assertTrue(np.array_equal(self.cf._E0, 6*a))

        b = np.eye(10)
        self.assertRaises(ValueError, self.cf.add_to, ("E", 0), b)
        self.cf.add_to(("E", 2), b)
        self.assertTrue(np.array_equal(self.cf._E2, b))
        self.cf.add_to(("E", 2), 2*b)
        self.assertTrue(np.array_equal(self.cf._E2, 3*b))

        f = np.array(range(5))
        self.assertRaises(ValueError, self.cf.add_to, ("E", 0), f)
        self.cf.add_to(("f", 0), f)
        self.assertTrue(np.array_equal(self.cf._f0, f))
        self.cf.add_to(("f", 0), 2*f)
        self.assertTrue(np.array_equal(self.cf._f0, 3*f))

    def test_get_terms(self):
        self.cf.add_to(("E", 0), np.eye(5))
        self.cf.add_to(("E", 2), 5*np.eye(5))
        terms = self.cf.get_terms()
        self.assertTrue(np.array_equal(terms[0][0], np.eye(5)))
        self.assertTrue(np.array_equal(terms[0][1], np.zeros((5, 5))))
        self.assertTrue(np.array_equal(terms[0][2], 5*np.eye(5)))
        self.assertEqual(terms[1], None)
        self.assertEqual(terms[2], None)


class ParseTest(unittest.TestCase):

    def setUp(self):
        # scalars
        self.scalars = sim.Scalars(np.vstack(range(3)))

        # inputs
        self.u = cr.Function(np.sin)
        self.input = sim.Input(self.u)  # control input

        # TestFunctions
        nodes, self.ini_funcs = ut.cure_interval(cr.LagrangeFirstOrder, (0, 1), node_count=3)
        self.phi = sim.TestFunctions(self.ini_funcs)  # eigenfunction or something else
        self.phi_at0 = sim.TestFunctions(self.ini_funcs, location=0)  # eigenfunction or something else
        self.phi_at1 = sim.TestFunctions(self.ini_funcs, location=1)  # eigenfunction or something else
        self.dphi = sim.TestFunctions(self.ini_funcs, order=1)  # eigenfunction or something else
        self.dphi_at1 = sim.TestFunctions(self.ini_funcs, order=1, location=1)  # eigenfunction or something else

        # FieldVars
        self.field_var = sim.FieldVariable(self.ini_funcs)
        self.field_var_at1 = sim.FieldVariable(self.ini_funcs, location=1)
        self.field_var_dz = sim.SpatialDerivedFieldVariable(self.ini_funcs, 1)
        self.field_var_dz_at1 = sim.SpatialDerivedFieldVariable(self.ini_funcs, 1, location=1)
        self.field_var_ddt = sim.TemporalDerivedFieldVariable(self.ini_funcs, 2)
        self.field_var_ddt_at0 = sim.TemporalDerivedFieldVariable(self.ini_funcs, 2, location=0)
        self.field_var_ddt_at1 = sim.TemporalDerivedFieldVariable(self.ini_funcs, 2, location=1)

        # create all possible kinds of input variables
        self.input_term1 = sim.ScalarTerm(sim.Product(self.phi_at1, self.input))
        self.input_term2 = sim.ScalarTerm(sim.Product(self.dphi_at1, self.input))
        self.func_term = sim.ScalarTerm(self.phi_at1)

        self.field_term_at1 = sim.ScalarTerm(self.field_var_at1)
        self.field_term_dz_at1 = sim.ScalarTerm(self.field_var_dz_at1)
        self.field_term_ddt_at1 = sim.ScalarTerm(self.field_var_ddt_at1)
        self.field_int = sim.IntegralTerm(self.field_var, (0, 1))
        self.field_dz_int = sim.IntegralTerm(self.field_var_dz, (0, 1))
        self.field_ddt_int = sim.IntegralTerm(self.field_var_ddt, (0, 1))

        self.prod_term_fs_at1 = sim.ScalarTerm(sim.Product(self.field_var_at1, self.scalars))
        self.prod_int_fs = sim.IntegralTerm(sim.Product(self.field_var, self.scalars), (0, 1))
        self.prod_int_f_f = sim.IntegralTerm(sim.Product(self.field_var, self.phi), (0, 1))
        self.prod_int_f_at1_f = sim.IntegralTerm(sim.Product(self.field_var_at1, self.phi), (0, 1))
        self.prod_int_f_f_at1 = sim.IntegralTerm(sim.Product(self.field_var, self.phi_at1), (0, 1))
        self.prod_term_f_at1_f_at1 = sim.ScalarTerm(sim.Product(self.field_var_at1, self.phi_at1))

        self.prod_int_fddt_f = sim.IntegralTerm(sim.Product(self.field_var_ddt, self.phi), (0, 1))
        self.prod_term_fddt_at0_f_at0 = sim.ScalarTerm(sim.Product(self.field_var_ddt_at0, self.phi_at0))

        self.prod_term_f_at1_dphi_at1 = sim.ScalarTerm(sim.Product(self.field_var_at1, self.dphi_at1))

        self.temp_int = sim.IntegralTerm(sim.Product(self.field_var_ddt, self.phi), (0, 1))
        self.spat_int = sim.IntegralTerm(sim.Product(self.field_var_dz, self.dphi), (0, 1))
        self.spat_int_asymmetric = sim.IntegralTerm(sim.Product(self.field_var_dz, self.phi), (0, 1))

    def test_Input_term(self):
        terms = sim.parse_weak_formulation(sim.WeakFormulation(self.input_term2)).get_terms()
        self.assertEqual(terms[0], None)  # E0
        self.assertEqual(terms[1], None)  # f
        self.assertTrue(np.allclose(terms[2][0], np.array([[0], [-2], [2]])))  # g

    def test_TestFunction_term(self):
        wf = sim.WeakFormulation(self.func_term)
        sim.parse_weak_formulation(wf)

    def test_FieldVariable_term(self):
        terms = sim.parse_weak_formulation(sim.WeakFormulation(self.field_term_at1)).get_terms()
        self.assertTrue(np.allclose(terms[0][0], np.array([[0, 0, 0], [0, 0, 0], [1, 1, 1]])))

        terms = sim.parse_weak_formulation(sim.WeakFormulation(self.field_int)).get_terms()
        self.assertTrue(np.allclose(terms[0][0], np.array([[0.25, 0.25, 0.25], [0.5, 0.5, 0.5], [.25, .25, .25]])))

        terms = sim.parse_weak_formulation(sim.WeakFormulation(self.field_term_dz_at1)).get_terms()
        self.assertTrue(np.allclose(terms[0][0], np.array([[0, 0, 0], [-2, -2, -2], [2, 2, 2]])))

        terms = sim.parse_weak_formulation(sim.WeakFormulation(self.field_dz_int)).get_terms()
        self.assertTrue(np.allclose(terms[0][0], np.array([[-1, -1, -1], [0, 0, 0], [1, 1, 1]])))

        terms = sim.parse_weak_formulation(sim.WeakFormulation(self.field_term_ddt_at1)).get_terms()
        self.assertTrue(np.allclose(terms[0][0], np.zeros((3, 3))))
        self.assertTrue(np.allclose(terms[0][1], np.zeros((3, 3))))
        self.assertTrue(np.allclose(terms[0][2], np.array([[0, 0, 0], [0, 0, 0], [1, 1, 1]])))

        terms = sim.parse_weak_formulation(sim.WeakFormulation(self.field_ddt_int)).get_terms()
        self.assertTrue(np.allclose(terms[0][0], np.zeros((3, 3))))
        self.assertTrue(np.allclose(terms[0][1], np.zeros((3, 3))))
        self.assertTrue(np.allclose(terms[0][2], np.array([[0.25, 0.25, 0.25], [0.5, 0.5, 0.5], [.25, .25, .25]])))

    def test_Product_term(self):
        # terms = sim.parse_weak_formulation(sim.WeakFormulation(self.prod_term_fs_at1)).get_terms()
        # self.assertTrue(np.allclose(terms[0][0], np.array([[0, 0, 0], [1, 0, 0], [2, 0, 0]])))

        terms = sim.parse_weak_formulation(sim.WeakFormulation(self.prod_int_fs)).get_terms()
        self.assertTrue(np.allclose(terms[0][0], np.array([[0, 0, 0], [0.25, .5, .25], [.5, 1, .5]])))

        terms = sim.parse_weak_formulation(sim.WeakFormulation(self.prod_int_f_f)).get_terms()
        self.assertTrue(np.allclose(terms[0][0], np.array([[1/6, 1/12, 0], [1/12, 1/3, 1/12], [0, 1/12, 1/6]])))

        terms = sim.parse_weak_formulation(sim.WeakFormulation(self.prod_int_f_at1_f)).get_terms()
        self.assertTrue(np.allclose(terms[0][0], np.array([[0, 0, 0.25], [0, 0, 0.5], [0, 0, .25]])))

        terms = sim.parse_weak_formulation(sim.WeakFormulation(self.prod_int_f_f_at1)).get_terms()
        self.assertTrue(np.allclose(terms[0][0], np.array([[0, 0, 0], [0, 0, 0], [0.25, 0.5, .25]])))

        terms = sim.parse_weak_formulation(sim.WeakFormulation(self.prod_term_f_at1_f_at1)).get_terms()
        self.assertTrue(np.allclose(terms[0][0], np.array([[0, 0, 0], [0, 0, 0], [0, 0, 1]])))

        # more complex terms
        terms = sim.parse_weak_formulation(sim.WeakFormulation(self.prod_int_fddt_f)).get_terms()
        self.assertTrue(np.allclose(terms[0][0], np.zeros((3, 3))))
        self.assertTrue(np.allclose(terms[0][1], np.zeros((3, 3))))
        self.assertTrue(np.allclose(terms[0][2], np.array([[1/6, 1/12, 0], [1/12, 1/3, 1/12], [0, 1/12, 1/6]])))
        self.assertEqual(terms[1], None)  # f
        self.assertEqual(terms[2], None)  # g

        terms = sim.parse_weak_formulation(sim.WeakFormulation(self.prod_term_fddt_at0_f_at0)).get_terms()
        self.assertTrue(np.allclose(terms[0][0], np.zeros((3, 3))))
        self.assertTrue(np.allclose(terms[0][1], np.zeros((3, 3))))
        self.assertTrue(np.allclose(terms[0][2], np.array([[1, 0, 0], [0, 0, 0], [0, 0, 0]])))
        self.assertEqual(terms[1], None)  # f
        self.assertEqual(terms[2], None)  # g

        terms = sim.parse_weak_formulation(sim.WeakFormulation(self.spat_int)).get_terms()
        self.assertTrue(np.allclose(terms[0][0], np.array([[2, -2, 0], [-2, 4, -2], [0, -2, 2]])))
        self.assertEqual(terms[1], None)  # f
        self.assertEqual(terms[2], None)  # g

        terms = sim.parse_weak_formulation(sim.WeakFormulation(self.spat_int_asymmetric)).get_terms()
        self.assertTrue(np.allclose(terms[0][0], np.array([[-.5, .5, 0], [-.5, 0, .5], [0, -.5, .5]])))
        self.assertEqual(terms[1], None)  # f
        self.assertEqual(terms[2], None)  # g

        terms = sim.parse_weak_formulation(sim.WeakFormulation(self.prod_term_f_at1_dphi_at1)).get_terms()
        self.assertTrue(np.allclose(terms[0][0], np.array([[0, 0, 0], [0, 0, -2], [0, 0, 2]])))
        self.assertEqual(terms[1], None)  # f
        self.assertEqual(terms[2], None)  # g

        terms = sim.parse_weak_formulation(sim.WeakFormulation(self.input_term1)).get_terms()
        self.assertEqual(terms[0], None)  # E
        self.assertEqual(terms[1], None)  # f
        self.assertTrue(np.allclose(terms[2][0], np.array([[0], [0], [1]])))

    def test_modal_form(self):
        pass


class StateSpaceTests(unittest.TestCase):

    def setUp(self):
        # enter string with mass equations
        self.u = cr.Function(lambda x: 0)
        interval = (0, 1)
        nodes, ini_funcs = ut.cure_interval(cr.LagrangeFirstOrder, interval, node_count=3)
        int1 = sim.IntegralTerm(sim.Product(sim.TemporalDerivedFieldVariable(ini_funcs, 2),
                                            sim.TestFunctions(ini_funcs)), interval)
        s1 = sim.ScalarTerm(sim.Product(sim.TemporalDerivedFieldVariable(ini_funcs, 2, location=0),
                                        sim.TestFunctions(ini_funcs, location=0)))
        int2 = sim.IntegralTerm(sim.Product(sim.SpatialDerivedFieldVariable(ini_funcs, 1),
                                            sim.TestFunctions(ini_funcs, order=1)), interval)
        s2 = sim.ScalarTerm(sim.Product(sim.Input(self.u), sim.TestFunctions(ini_funcs, location=1)), -1)

        string_pde = sim.WeakFormulation([int1, s1, int2, s2])
        self.cf = sim.parse_weak_formulation(string_pde)

    def test_convert_to_state_space(self):
        ss = self.cf.convert_to_state_space()
        self.assertTrue(np.allclose(ss.A, np.array([[0, 0, 0, 1, 0, 0],
                                                    [0, 0, 0, 0, 1, 0],
                                                    [0, 0, 0, 0, 0, 1],
                                                    [-2.25, 3, -.75, 0, 0, 0],
                                                    [7.5, -18, 10.5, 0, 0, 0],
                                                    [-3.75, 21, -17.25, 0, 0, 0]])))
        self.assertTrue(np.allclose(ss.B, np.array([[0], [0], [0], [0.125], [-1.75], [6.875]])))
        self.assertEqual(self.cf.input_function, self.u)


class StringMassTest(unittest.TestCase):

    def setUp(self):
        self.app = pg.QtGui.QApplication([])

        z_start = 0
        z_end = 1
        t_start = 0
        t_end = 5
        z_step = 0.01
        t_step = 0.01
        self.t_values = np.arange(t_start, t_end+t_step, t_step)
        self.z_values = np.arange(z_start, z_end+z_step, z_step)
        self.node_distance = 0.1
        self.mass = 1.0
        self.order = 8
        self.temp_interval = (t_start, t_end)
        self.spat_interval = (z_start, z_end)

        fs = tr.FlatString(0, 10, 0, 3, m=self.mass)
        self.u = cr.Function(fs.control_input)

        def x(z, t):
            """
            initial conditions for testing
            """
            return 0

        def x_dt(z, t):
            """
            initial conditions for testing
            """
            return 0

        # initial conditions
        self.ic = np.array([
            cr.Function(lambda z: x(z, 0)),  # x(z, 0)
            cr.Function(lambda z: x_dt(z, 0)),  # dx_dt(z, 0)
        ])

    def test_fem(self):
        """
        use best documented fem case to test all steps in simulation process
        """

        # enter string with mass equations
        nodes, ini_funcs = ut.cure_interval(cr.LagrangeFirstOrder, self.spat_interval, node_count=10)
        int1 = sim.IntegralTerm(sim.Product(sim.TemporalDerivedFieldVariable(ini_funcs, 2),
                                            sim.TestFunctions(ini_funcs)), self.spat_interval)
        s1 = sim.ScalarTerm(sim.Product(sim.TemporalDerivedFieldVariable(ini_funcs, 2, location=0),
                                        sim.TestFunctions(ini_funcs, location=0)))
        int2 = sim.IntegralTerm(sim.Product(sim.SpatialDerivedFieldVariable(ini_funcs, 1),
                                            sim.TestFunctions(ini_funcs, order=1)), self.spat_interval)
        s2 = sim.ScalarTerm(sim.Product(sim.Input(self.u), sim.TestFunctions(ini_funcs, location=1)), -1)

        # derive sate-space system
        string_pde = sim.WeakFormulation([int1, s1, int2, s2])
        self.cf = sim.parse_weak_formulation(string_pde)
        ss = self.cf.convert_to_state_space()

        # generate initial conditions for weights
        q0 = np.array([cr.project_on_initial_functions(self.ic[idx], ini_funcs) for idx in range(2)]).flatten()

        # simulate
        t, q = sim.simulate_state_space(ss, self.cf.input_function, q0, self.temp_interval)

        # calculate result data
        eval_data = []
        for der_idx in range(2):
            eval_data.append(ut.evaluate_approximation(q[:, der_idx*ini_funcs.size:(der_idx+1)*ini_funcs.size],
                                                       ini_funcs, t, self.z_values))
            eval_data[-1].name = "{0}{1}".format(self.cf.name, "_"+"".join(["d" for x in range(der_idx)])+"t")

        # display results
        if show_plots:
            win = vis.AnimatedPlot(eval_data[:2], title="fem approx and derivative")
            win2 = vis.SurfacePlot(eval_data[0])
            self.app.exec_()

    def test_modal(self):
        order = 8

        def char_eq(w):
            return w * (np.sin(w) + self.mass * w * np.cos(w))

        def phi_k_factory(freq, derivative_order=0):
            def eig_func(z):
                return np.cos(freq * z) - self.mass * freq * np.sin(freq * z)

            def eig_func_dz(z):
                return -freq * (np.sin(freq * z) + self.mass * freq * np.cos(freq * z))

            def eig_func_ddz(z):
                return freq ** 2 * (-np.cos(freq * z) + self.mass * freq * np.sin(freq * z))

            if derivative_order == 0:
                return eig_func
            elif derivative_order == 1:
                return eig_func_dz
            elif derivative_order == 2:
                return eig_func_ddz
            else:
                raise ValueError

        # create eigenfunctions
        eig_frequencies = ut.find_roots(char_eq, order)
        print("eigenfrequencies:")
        print eig_frequencies

        # create eigen function vectors
        class SWMFunctionVector(cr.ComposedFunctionVector):
            """
            String With Mass Function Vector, necessary due to manipulated scalar product
            """

            @staticmethod
            def scalar_product(first, second):
                if not isinstance(first, SWMFunctionVector) or not isinstance(second, cr.ComposedFunctionVector):
                    raise TypeError("only SWMFunctionVector supported")
                return cr.dot_product_l2(first.members[0], second.members[0]) + self.mass * first.members[1] * \
                                                                                second.members[1]

        eig_vectors = []
        for n in range(order):
            eig_vectors.append(SWMFunctionVector(cr.Function(phi_k_factory(eig_frequencies[n]),
                                                             derivative_handles=[
                                                                 phi_k_factory(eig_frequencies[n], der_order)
                                                                 for der_order in range(1, 3)],
                                                             domain=self.spat_interval,
                                                             nonzero=self.spat_interval),
                                                 phi_k_factory(eig_frequencies[n])(0)))

        # normalize eigen vectors
        norm_eig_vectors = [cr.normalize_function(vec) for vec in eig_vectors]
        norm_eig_funcs = np.atleast_1d([vec.members[0] for vec in norm_eig_vectors])

        # debug print eigenfunctions
        if 0:
            func_vals = []
            for vec in eig_vectors:
                func_vals.append(np.vectorize(vec.members[0])(self.z_values))

            norm_func_vals = []
            for func in norm_eig_funcs:
                norm_func_vals.append(np.vectorize(func)(self.z_values))

            clrs = ["r", "g", "b", "c", "m", "y", "k", "w"]
            for n in range(1, order + 1, len(clrs)):
                pw_phin_k = pg.plot(title="phin_k for k in [{0}, {1}]".format(n, min(n + len(clrs), order)))
                for k in range(len(clrs)):
                    if k + n > order:
                        break
                    pw_phin_k.plot(x=self.z_values, y=norm_func_vals[n + k - 1], pen=clrs[k])

            self.app.exec_()

        # create terms of weak formulation
        terms = [sim.IntegralTerm(sim.Product(sim.FieldVariable(norm_eig_funcs, order=(2, 0)),
                                              sim.TestFunctions(norm_eig_funcs)),
                                  self.spat_interval, scale=-1),
                 sim.ScalarTerm(sim.Product(sim.FieldVariable(norm_eig_funcs, order=(2, 0), location=0),
                                            sim.TestFunctions(norm_eig_funcs, location=0)),
                                scale=-1), sim.ScalarTerm(sim.Product(sim.Input(self.u),
                                                                      sim.TestFunctions(norm_eig_funcs, location=1))),
                 sim.ScalarTerm(sim.Product(sim.FieldVariable(norm_eig_funcs, location=1),
                                            sim.TestFunctions(norm_eig_funcs, order=1, location=1)),
                                scale=-1), sim.ScalarTerm(sim.Product(sim.FieldVariable(norm_eig_funcs, location=0),
                                                                      sim.TestFunctions(norm_eig_funcs, order=1,
                                                                                        location=0))),
                 sim.IntegralTerm(sim.Product(sim.FieldVariable(norm_eig_funcs),
                                              sim.TestFunctions(norm_eig_funcs, order=2)),
                                  self.spat_interval)]
        modal_pde = sim.WeakFormulation(terms, name="swm_lib-modal")
        eval_data = sim.simulate_system(modal_pde, self.ic, self.temp_interval, self.z_values)

        # display results
        if show_plots:
            win = vis.AnimatedPlot(eval_data[0:2], title="modal approx and derivative")
            win2 = vis.SurfacePlot(eval_data[0])
            self.app.exec_()

    def tearDown(self):
        del self.app

    # TODO test "forbidden" terms like derivatives on the borders
