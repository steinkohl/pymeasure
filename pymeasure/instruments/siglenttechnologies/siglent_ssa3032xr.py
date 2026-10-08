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

from pymeasure.instruments import Channel, Instrument, SCPIMixin
from pymeasure.instruments.validators import strict_discrete_set, strict_range

_TRACE_MODES = ["WRITE", "MAXHOLD", "MINHOLD", "VIEW", "BLANK", "AVERAGE"]
_RESOLUTION_BANDWIDTHS = [10, 30, 100, 300, 1e3, 3e3, 10e3, 30e3, 100e3, 300e3, 1e6]
_VIDEO_BANDWIDTHS = [1, 3, *_RESOLUTION_BANDWIDTHS]
_AMPLITUDE_UNITS = ["DBM", "DBMV", "DBUV", "V", "W"]


class Marker(Channel):
    """Marker of the Siglent SSA3000X-R series spectrum analyzers."""

    enabled = Instrument.control(
        ":CALCulate:MARKer{ch}:STATe?", ":CALCulate:MARKer{ch}:STATe %d",
        """Control whether the marker is shown (bool).""",
        validator=strict_discrete_set,
        values={True: 1, False: 0},
        map_values=True,
    )

    x = Instrument.control(
        ":CALCulate:MARKer{ch}:X?", ":CALCulate:MARKer{ch}:X %g",
        """Control the marker position on the frequency axis in Hz (float).""",
    )

    y = Instrument.measurement(
        ":CALCulate:MARKer{ch}:Y?",
        """Measure the amplitude at the marker position in the current amplitude unit (float).""",
    )

    def peak_search(self):
        """Move the marker to the maximum of the trace."""
        self.write(":CALCulate:MARKer{ch}:MAXimum")


class Trace(Channel):
    """Trace of the Siglent SSA3000X-R series spectrum analyzers."""

    mode = Instrument.control(
        ":TRACe{ch}:MODE?", ":TRACe{ch}:MODE %s",
        """Control the trace mode (strictly one of 'WRITE', 'MAXHOLD', 'MINHOLD', 'VIEW',
        'BLANK', 'AVERAGE').""",
        validator=strict_discrete_set,
        values=_TRACE_MODES,
        cast=str,
        # SCPI replies may use the short or long form; the first four letters are unique
        get_process=lambda v: next(m for m in _TRACE_MODES if m[:4] == v.strip().upper()[:4]),
    )


class SSA3032XR(SCPIMixin, Instrument):
    """Represent the Siglent SSA3032X-R real-time spectrum analyzer.

    The instrument is controlled via SCPI over LAN (raw socket or VISA) or USB.
    The same command set applies to the other SSA3000X-R models.

    .. code-block:: python

        sa = SSA3032XR("TCPIP::192.168.1.10::INSTR")
        sa.freq_center = 100e6
        sa.freq_span = 10e6
        sa.single_sweep()
        frequency, amplitude = sa.read_trace()
        sa.marker_1.enabled = True
        sa.marker_1.peak_search()
        print(sa.marker_1.x, sa.marker_1.y)
    """

    trace_1 = Instrument.ChannelCreator(Trace, 1)
    trace_2 = Instrument.ChannelCreator(Trace, 2)
    trace_3 = Instrument.ChannelCreator(Trace, 3)
    trace_4 = Instrument.ChannelCreator(Trace, 4)

    marker_1 = Instrument.ChannelCreator(Marker, 1)
    marker_2 = Instrument.ChannelCreator(Marker, 2)
    marker_3 = Instrument.ChannelCreator(Marker, 3)
    marker_4 = Instrument.ChannelCreator(Marker, 4)

    freq_limits = [0, 3.2e9]
    trace_numbers = [1, 2, 3, 4]

    def __init__(self, adapter, name="Siglent SSA3032X-R Spectrum Analyzer", **kwargs):
        super().__init__(adapter, name, **kwargs)

    # Frequency ------------------------------------------------------------------------------

    freq_center = Instrument.control(
        ":FREQuency:CENTer?", ":FREQuency:CENTer %g",
        """Control the center frequency in Hz (float strictly from 0 to 3.2e9).""",
        validator=strict_range,
        values=freq_limits,
    )

    freq_span = Instrument.control(
        ":FREQuency:SPAN?", ":FREQuency:SPAN %g",
        """Control the frequency span in Hz (float strictly from 0 to 3.2e9).""",
        validator=strict_range,
        values=freq_limits,
    )

    freq_start = Instrument.control(
        ":FREQuency:STARt?", ":FREQuency:STARt %g",
        """Control the start frequency in Hz (float strictly from 0 to 3.2e9).""",
        validator=strict_range,
        values=freq_limits,
    )

    freq_stop = Instrument.control(
        ":FREQuency:STOP?", ":FREQuency:STOP %g",
        """Control the stop frequency in Hz (float strictly from 0 to 3.2e9).""",
        validator=strict_range,
        values=freq_limits,
    )

    def full_span(self):
        """Set the frequency span to the full span of the instrument."""
        self.write(":FREQuency:SPAN:FULL")

    # Bandwidth and sweep --------------------------------------------------------------------

    resolution_bandwidth = Instrument.control(
        ":BWIDth:RESolution?", ":BWIDth:RESolution %g",
        """Control the resolution bandwidth in Hz (strictly 10, 30, 100, 300 ... 300e3, 1e6).""",
        validator=strict_discrete_set,
        values=_RESOLUTION_BANDWIDTHS,
    )

    resolution_bandwidth_auto = Instrument.control(
        ":BWIDth:RESolution:AUTO?", ":BWIDth:RESolution:AUTO %d",
        """Control whether the resolution bandwidth is coupled automatically (bool).""",
        validator=strict_discrete_set,
        values={True: 1, False: 0},
        map_values=True,
    )

    video_bandwidth = Instrument.control(
        ":BWIDth:VIDeo?", ":BWIDth:VIDeo %g",
        """Control the video bandwidth in Hz (strictly 1, 3, 10, 30 ... 300e3, 1e6).""",
        validator=strict_discrete_set,
        values=_VIDEO_BANDWIDTHS,
    )

    video_bandwidth_auto = Instrument.control(
        ":BWIDth:VIDeo:AUTO?", ":BWIDth:VIDeo:AUTO %d",
        """Control whether the video bandwidth is coupled automatically (bool).""",
        validator=strict_discrete_set,
        values={True: 1, False: 0},
        map_values=True,
    )

    sweep_time = Instrument.control(
        ":SWEep:TIME?", ":SWEep:TIME %g",
        """Control the sweep time in s (float strictly from 917e-6 to 1000).""",
        validator=strict_range,
        values=[917e-6, 1000],
    )

    sweep_time_auto = Instrument.control(
        ":SWEep:TIME:AUTO?", ":SWEep:TIME:AUTO %d",
        """Control whether the sweep time is coupled automatically (bool).""",
        validator=strict_discrete_set,
        values={True: 1, False: 0},
        map_values=True,
    )

    continuous_sweep_enabled = Instrument.control(
        ":INITiate:CONTinuous?", ":INITiate:CONTinuous %d",
        """Control whether the sweep runs continuously (True) or as single sweep (False).""",
        validator=strict_discrete_set,
        values={True: 1, False: 0},
        map_values=True,
    )

    def single_sweep(self):
        """Switch to single sweep mode, start a sweep and wait until it is finished."""
        self.continuous_sweep_enabled = False
        self.write(":INITiate:IMMediate")
        self.complete  # noqa: B018 - reading *OPC? blocks until the sweep is done

    # Amplitude ------------------------------------------------------------------------------

    amplitude_unit = Instrument.control(
        ":UNIT:POWer?", ":UNIT:POWer %s",
        """Control the amplitude unit (strictly one of 'DBM', 'DBMV', 'DBUV', 'V', 'W').""",
        validator=strict_discrete_set,
        values=_AMPLITUDE_UNITS,
        cast=str,
        get_process=lambda v: v.upper(),
    )

    reference_level = Instrument.control(
        ":DISPlay:WINDow:TRACe:Y:SCALe:RLEVel?", ":DISPlay:WINDow:TRACe:Y:SCALe:RLEVel %g",
        """Control the reference level in the current amplitude unit (float).""",
    )

    scale_per_division = Instrument.control(
        ":DISPlay:WINDow:TRACe:Y:SCALe:PDIVision?", ":DISPlay:WINDow:TRACe:Y:SCALe:PDIVision %g",
        """Control the vertical scale in dB per division (float strictly from 1 to 10).""",
        validator=strict_range,
        values=[1, 10],
    )

    attenuation = Instrument.control(
        ":POWer:ATTenuation?", ":POWer:ATTenuation %d",
        """Control the input attenuation in dB (int strictly from 0 to 50).""",
        validator=strict_discrete_set,
        values=range(51),
        cast=int,
    )

    attenuation_auto = Instrument.control(
        ":POWer:ATTenuation:AUTO?", ":POWer:ATTenuation:AUTO %d",
        """Control whether the input attenuation is coupled automatically (bool).""",
        validator=strict_discrete_set,
        values={True: 1, False: 0},
        map_values=True,
    )

    preamplifier_enabled = Instrument.control(
        ":POWer:GAIN?", ":POWer:GAIN %d",
        """Control whether the preamplifier is enabled (bool).""",
        validator=strict_discrete_set,
        values={True: 1, False: 0},
        map_values=True,
    )

    # Trigger --------------------------------------------------------------------------------

    trigger_source = Instrument.control(
        ":TRIGger:SOURce?", ":TRIGger:SOURce %s",
        """Control the trigger source (strictly 'internal' for free run or 'external').""",
        validator=strict_discrete_set,
        values=["internal", "external"],
        set_process=lambda v: {"internal": "IMMediate", "external": "EXTernal"}[v],
        cast=str,
        # The reply may be in short or long form; 'video' can only be set on the front panel
        get_process=lambda v: {"IMM": "internal", "EXT": "external"}.get(
            v.strip().upper()[:3], v.strip().lower()),
    )

    # System ---------------------------------------------------------------------------------

    def power_off(self):
        """Turn off the instrument."""
        self.write(":SYSTem:POWer:OFF")

    def shutdown(self):
        """Bring the instrument to a safe state: continuous sweep and internal trigger."""
        self.continuous_sweep_enabled = True
        self.trigger_source = "internal"
        super().shutdown()

    # Traces ---------------------------------------------------------------------------------

    def read_trace(self, trace=1):
        """Read the amplitude data of a trace together with its frequency axis.

        :param int trace: Trace number (1 to 4).
        :return: 2d numpy array ``[frequency in Hz, amplitude]`` in the current amplitude unit.
        """
        trace = strict_discrete_set(trace, self.trace_numbers)
        self.write(":FORMat ASCii")
        amplitude = np.array(self.values(f":TRACe:DATA? {trace}"), dtype=float)
        frequency = np.linspace(self.freq_start, self.freq_stop, len(amplitude))
        return np.array([frequency, amplitude])
