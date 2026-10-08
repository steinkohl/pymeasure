#
# This file is part of the PyMeasure package.
#
# Copyright (c) 2013-2026 PyMeasure Developers
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

import numpy as np
import pytest

from pymeasure.instruments.siglenttechnologies import SSA3032XR
from pymeasure.test import expected_protocol


def test_freq_center():
    with expected_protocol(
        SSA3032XR,
        [(":FREQuency:CENTer 1e+08", None),
         (":FREQuency:CENTer?", "100000000")],
    ) as inst:
        inst.freq_center = 100e6
        assert inst.freq_center == 100e6


def test_freq_span_out_of_range():
    with expected_protocol(SSA3032XR, []) as inst, pytest.raises(ValueError):
        inst.freq_span = 4e9


def test_resolution_bandwidth_auto():
    with expected_protocol(
        SSA3032XR,
        [(":BWIDth:RESolution:AUTO 1", None),
         (":BWIDth:RESolution:AUTO?", "1")],
    ) as inst:
        inst.resolution_bandwidth_auto = True
        assert inst.resolution_bandwidth_auto is True


def test_resolution_bandwidth():
    with expected_protocol(
        SSA3032XR,
        [(":BWIDth:RESolution 1000", None),
         (":BWIDth:RESolution?", "1000")],
    ) as inst:
        inst.resolution_bandwidth = 1e3
        assert inst.resolution_bandwidth == 1e3


def test_resolution_bandwidth_not_discrete():
    with expected_protocol(SSA3032XR, []) as inst, pytest.raises(ValueError):
        inst.resolution_bandwidth = 2e3


def test_attenuation_out_of_range():
    with expected_protocol(SSA3032XR, []) as inst, pytest.raises(ValueError):
        inst.attenuation = 51


def test_single_sweep():
    with expected_protocol(
        SSA3032XR,
        [(":INITiate:CONTinuous 0", None),
         (":INITiate:IMMediate", None),
         ("*OPC?", "1")],
    ) as inst:
        inst.single_sweep()


def test_amplitude_unit():
    with expected_protocol(
        SSA3032XR,
        [(":UNIT:POWer DBMV", None),
         (":UNIT:POWer?", "DBMV")],
    ) as inst:
        inst.amplitude_unit = "DBMV"
        assert inst.amplitude_unit == "DBMV"


def test_attenuation():
    with expected_protocol(
        SSA3032XR,
        [(":POWer:ATTenuation 10", None),
         (":POWer:ATTenuation?", "10")],
    ) as inst:
        inst.attenuation = 10
        assert inst.attenuation == 10


def test_trace_mode():
    with expected_protocol(
        SSA3032XR,
        [(":TRACe2:MODE MAXHOLD", None),
         (":TRACe2:MODE?", "MAXH")],
    ) as inst:
        inst.trace_2.mode = "MAXHOLD"
        assert inst.trace_2.mode == "MAXHOLD"


def test_read_trace():
    with expected_protocol(
        SSA3032XR,
        [(":FORMat ASCii", None),
         (":TRACe:DATA? 1", "-50.0,-40.0,-60.0"),
         (":FREQuency:STARt?", "0"),
         (":FREQuency:STOP?", "100")],
    ) as inst:
        trace = inst.read_trace(1)
        np.testing.assert_allclose(trace, [[0, 50, 100], [-50, -40, -60]])


def test_marker_peak_search():
    with expected_protocol(
        SSA3032XR,
        [(":CALCulate:MARKer1:STATe 1", None),
         (":CALCulate:MARKer1:MAXimum", None),
         (":CALCulate:MARKer1:X?", "1000000"),
         (":CALCulate:MARKer1:Y?", "-12.5")],
    ) as inst:
        inst.marker_1.enabled = True
        inst.marker_1.peak_search()
        assert inst.marker_1.x == 1e6
        assert inst.marker_1.y == -12.5
