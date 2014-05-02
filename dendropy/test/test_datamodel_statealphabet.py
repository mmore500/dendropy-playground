#! /usr/bin/env python

##############################################################################
##  DendroPy Phylogenetic Computing Library.
##
##  Copyright 2010 Jeet Sukumaran and Mark T. Holder.
##  All rights reserved.
##
##  See "LICENSE.txt" for terms and conditions of usage.
##
##  If you use this work or any portion thereof in published work,
##  please cite it as:
##
##     Sukumaran, J. and M. T. Holder. 2010. DendroPy: a Python library
##     for phylogenetic computing. Bioinformatics 26: 1569-1571.
##
##############################################################################

"""
Tests Tree taxon management
"""

import itertools
import unittest
import collections
import dendropy
from dendropy.test.support import dendropytest

class StateAlphabetTester(object):

    def validate_state_identities(self,
            state_container,
            state_iter,
            symbol_iter,
            expected_symbols,
            expected_denomination,
            member_state_map,
            additional_synonyms_map,
            case_sensitive=True):
        self.assertEqual(len(state_container), len(expected_symbols))
        states = list(state_iter())
        self.assertEqual(len(states), len(expected_symbols))
        canonical_symbols = list(symbol_iter(include_synonyms=False))
        self.assertEqual(canonical_symbols, expected_symbols)
        for state, symbol in zip(states, expected_symbols):
            all_synonyms = []
            self.assertEqual(state.symbol, symbol)
            self.assertEqual(state.state_denomination, expected_denomination)
            if member_state_map:
                expected_member_state_symbols = frozenset(member_state_map[symbol])
                self.assertEqual(state.fundamental_symbols, expected_member_state_symbols)
                fundamental_states = self.sa.get_fundamental_state_set_for_symbols(state.symbol)
                fss = [fs.symbol for fs in fundamental_states]
                self.assertEqual(set(fss), expected_member_state_symbols)
            else:
                self.assertEqual(state.fundamental_states, set([state]))
                self.assertEqual(state.fundamental_symbols, set([state.symbol]))
            if case_sensitive:
                self.assertNotIn(symbol.upper(), state.symbol_synonyms)
                self.assertNotIn(symbol.lower(), state.symbol_synonyms)
            else:
                if symbol.upper() != symbol:
                    self.assertIn(symbol.upper(), state.symbol_synonyms)
                    all_synonyms.append(symbol.upper())
                if symbol.lower() != symbol:
                    self.assertIn(symbol.lower(), state.symbol_synonyms)
                    all_synonyms.append(symbol.lower())
            if additional_synonyms_map:
                x = additional_synonyms_map.get(state.symbol, None)
                if x is not None:
                    all_synonyms.extend(x)
            self.assertEqual(set(all_synonyms), set(state.symbol_synonyms),
                    state)
            self.assertEqual(len(all_synonyms), len(state.symbol_synonyms), state.symbol)

            expected_fundamental_state_symbols = member_state_map.get(state.symbol, None)
            if expected_fundamental_state_symbols is None:
                expected_fundamental_states = set()
            else:
                expected_fundamental_states = self.sa.get_states_for_symbols(expected_fundamental_state_symbols)
                check_ss = [x.symbol for x in expected_fundamental_states]
                self.assertEqual(set(check_ss), set(expected_fundamental_state_symbols))

            fundamental_states = self.sa.get_fundamental_state_set_for_symbols(state.symbol)

    def test_fundamental_state_definitions(self):
        self.validate_state_identities(
                state_container=self.sa._fundamental_states,
                state_iter=self.sa.fundamental_state_iter,
                symbol_iter=self.sa.fundamental_symbol_iter,
                expected_symbols=self.expected_fundamental_state_symbols,
                expected_denomination=self.sa.FUNDAMENTAL_STATE,
                member_state_map={},
                additional_synonyms_map=self.additional_synonyms_map,
                case_sensitive=False)

    def test_ambiguous_state_definitions(self):
        self.validate_state_identities(
                state_container=self.sa._ambiguous_states,
                state_iter=self.sa.ambiguous_state_iter,
                symbol_iter=self.sa.ambiguous_symbol_iter,
                expected_symbols=self.expected_ambiguous_state_symbols,
                expected_denomination=self.sa.AMBIGUOUS_STATE,
                member_state_map=self.ambiguous_symbol_mappings,
                additional_synonyms_map=self.additional_synonyms_map,
                case_sensitive=False)

    def test_polymorphic_state_definitions(self):
        self.validate_state_identities(
                state_container=self.sa._polymorphic_states,
                state_iter=self.sa.polymorphic_state_iter,
                symbol_iter=self.sa.polymorphic_symbol_iter,
                expected_symbols=self.expected_polymorphic_state_symbols,
                expected_denomination=self.sa.POLYMORPHIC_STATE,
                member_state_map=self.polymorphic_symbol_mappings,
                additional_synonyms_map=self.additional_synonyms_map,
                case_sensitive=False)

    def test_symbol_iter(self):
        # assumes that the state iterators -- fundamental_state_iter,
        # ambiguous_state_iter, etc. -- all work as advertised
        iter_groups = (
                (self.sa.fundamental_symbol_iter, self.sa.fundamental_state_iter),
                (self.sa.ambiguous_symbol_iter, self.sa.ambiguous_state_iter),
                (self.sa.polymorphic_symbol_iter, self.sa.polymorphic_state_iter),
                (self.sa.multistate_symbol_iter, self.sa.multistate_state_iter),
                )
        for symbol_iter, state_iter in iter_groups:
            states = list(state_iter())
            for include_synonyms in (False, True):
                expected_symbols = []
                for state in states:
                    if state.symbol:
                        expected_symbols.append(state.symbol)
                    if include_synonyms:
                        for ss in state.symbol_synonyms:
                            expected_symbols.append(ss)
                obs_symbols = list(symbol_iter(include_synonyms=include_synonyms))
                self.assertEqual(expected_symbols, obs_symbols)

    def test_symbol_state_pair_iter(self):
        states = list(self.sa.state_iter())
        for include_synonyms in (False, True):
            expected_pairs = []
            for state in states:
                if state.symbol:
                    expected_pairs.append((state.symbol, state,))
                if include_synonyms:
                    for ss in state.symbol_synonyms:
                        expected_pairs.append((ss, state,))
            obs_pairs = list(self.sa.symbol_state_pair_iter(include_synonyms=include_synonyms))
            self.assertEqual(expected_pairs, obs_pairs)

    def test_state_iter(self):
        states = list(self.sa.state_iter())
        self.assertEqual(len(states), self.num_total_states)
        self.assertEqual(len(self.sa), len(states))
        expected_state_symbol_iter = itertools.chain(
                self.expected_fundamental_state_symbols,
                self.ambiguous_symbol_mappings,
                self.polymorphic_symbol_mappings
                )
        for state, symbol in zip(states, expected_state_symbol_iter):
            self.assertEqual(state.symbol, symbol)

    def test_state_denomination_for_state(self):
        for state in self.sa.fundamental_state_iter():
            self.assertEqual(state.state_denomination, self.sa.FUNDAMENTAL_STATE)
        for state in self.sa.ambiguous_state_iter():
            self.assertEqual(state.state_denomination, self.sa.AMBIGUOUS_STATE)
        for state in self.sa.polymorphic_state_iter():
            self.assertEqual(state.state_denomination, self.sa.POLYMORPHIC_STATE)

    def test_state_getitem_for_state(self):
        alphabet = self.sa
        for state in self.sa.state_iter():
            self.assertIs(alphabet[state.symbol], state)
            for ss in state.symbol_synonyms:
                self.assertIs(alphabet[ss], state)
            if state._index is not None:
                self.assertIs(alphabet[state._index], state)

    def validate_get_states_for_symbol_for_state(self, state):
        states_for_symbols = alphabet.get_states_for_symbols(state.symbol)
        self.assertEqual(len(states_for_symbols), 1)
        self.assertIs(states_for_symbols[0], state)

class DnaStateAlphabetTest(
        StateAlphabetTester,
        dendropytest.ExtendedTestCase):

    def setUp(self):
        self.expected_fundamental_state_symbols = ["A", "C", "G", "T", "-"]

        self.ambiguous_symbol_mappings = collections.OrderedDict()
        self.ambiguous_symbol_mappings["?"] = "ACGT-"
        self.ambiguous_symbol_mappings["N"] = "ACGT"
        self.ambiguous_symbol_mappings["R"] = "AG"
        self.ambiguous_symbol_mappings["Y"] = "CT"
        self.ambiguous_symbol_mappings["M"] = "AC"
        self.ambiguous_symbol_mappings["W"] = "AT"
        self.ambiguous_symbol_mappings["S"] = "CG"
        self.ambiguous_symbol_mappings["K"] = "GT"
        self.ambiguous_symbol_mappings["V"] = "ACG"
        self.ambiguous_symbol_mappings["H"] = "ACT"
        self.ambiguous_symbol_mappings["D"] = "AGT"
        self.ambiguous_symbol_mappings["B"] = "CGT"

        self.polymorphic_symbol_mappings = collections.OrderedDict()

        # note reverse polarity here: from referenced to referencing
        self.additional_synonyms_map = collections.OrderedDict()
        self.additional_synonyms_map["N"] = "X"

        self.expected_polymorphic_state_symbols = list(self.polymorphic_symbol_mappings.keys())
        self.expected_ambiguous_state_symbols = list(self.ambiguous_symbol_mappings.keys())

        self.sa = dendropy.DNA_STATE_ALPHABET
        self.num_total_states = len(self.expected_fundamental_state_symbols) + len(self.ambiguous_symbol_mappings) + len(self.polymorphic_symbol_mappings)

if __name__ == "__main__":
    unittest.main()
