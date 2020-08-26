from note_seq import Performance
from note_seq.performance_controls import PerformanceControlSignal
from note_seq import constants
from note_seq import encoder_decoder
from note_seq.performance_lib import PerformanceEvent
import math
import numbers
SPRITED = 0

class TimeEmbbedingPerformance(Performance):
  """Time embbeding Performance with absolute timing and unknown meter."""

  def __init__(self, quantized_sequence=None, steps_per_second=None,
               start_step=0, num_velocity_bins=0,instrument=None,
               program=None, is_drum=None):
    """Construct a Performance.
    Either quantized_sequence or steps_per_second should be supplied.
    Args:
      quantized_sequence: A quantized NoteSequence proto.
      steps_per_second: Number of quantized time steps per second, if using
          absolute quantization.
      start_step: The offset of this sequence relative to the
          beginning of the source sequence. If a quantized sequence is used as
          input, only notes starting after this step will be considered.
      num_velocity_bins: Number of velocity bins to use. If 0, velocity events
          will not be included at all.
      max_shift_steps: Maximum number of steps for a single time-shift event.
      instrument: If not None, extract only the specified instrument from
          `quantized_sequence`. Otherwise, extract all instruments.
      program: MIDI program used for this performance, or None if not specified.
          Ignored if `quantized_sequence` is provided.
      is_drum: Whether or not this performance consists of drums, or None if not
          specified. Ignored if `quantized_sequence` is provided.
    Raises:
      ValueError: If both or neither of `quantized_sequence` or
          `steps_per_second` is specified.
    """
    if hasattr(quantized_sequence,"subsequence_info.start_time_offset"):
        self._start_time_offset = quantized_sequence.subsequence_info.start_time_offset
        SPRITED += 1
        if SPRITED % 100 == 0:
            print("\r{0}".format(SPRITED), end="")
    else:
        self._start_time_offset = 0.0

    if hasattr(quantized_sequence,"subsequence_info.end_time_offset"):
        self._end_time = quantized_sequence.subsequence_info.end_time_offset + self._start_time_offset + quantized_sequence.total_time
    else:
        self._end_time = self._start_time_offset + quantized_sequence.total_time


    super(TimeEmbbedingPerformance, self).__init__(
        quantized_sequence=quantized_sequence,
        steps_per_second=steps_per_second,
        start_step=start_step,
        num_velocity_bins=num_velocity_bins,
        instrument=instrument,
        program=program,
        is_drum=is_drum)

  @property
  def start_time_offset(self):
      return self._start_time_offset
  @property
  def end_time(self):
      return self._end_time

class AbsoluteTimePerformanceControlSignal(PerformanceControlSignal):
  """Time embbeding performance control signal."""

  name = 'notes_per_second'
  description = 'Desired number of notes per second.'

  def __init__(self, max_dulation, time_embbeding_bin):
    """Initialize a NoteDensityPerformanceControlSignal.
    Args:
      window_size_seconds: The size of the window, in seconds, used to compute
          note density (notes per second).
      density_bin_ranges: List of note density (notes per second) bin boundaries
          to use when quantizing. The number of bins will be one larger than the
          list length.
    """
    self._max_dulation = max_dulation
    self._encoder = encoder_decoder.OneHotEventSequenceEncoderDecoder(
        self.AbsoluteTimeOneHotEncoding(time_embbeding_bin))

  def validate(self, value):
    return isinstance(value, numbers.Number) and value >= 0.0

  @property
  def encoder(self):
    return self._encoder

  def extract(self, performance):
    """Computes note density at every event in a performance.
    Args:
      performance: A Performance object for which to compute a note density
          sequence.
    Returns:
      A list of note densities of the same length as `performance`, with each
      entry equal to the note time step
    """
    assert hasattr(performance,"start_time_offset") ,"To use absolutely time embbeding, performance mast have start time offset and end time"
    steps_per_second = performance.steps_per_second
    current_step = performance.start_time_offset * steps_per_second
    max_step = self._max_dulation * steps_per_second

    absolute_time_sequence = []

    for event in performance:
      assert current_step < max_step, "Max step mast be largest than any dataset"
      absolute_time_sequence.append(current_step/max_step)
      if event.event_type == PerformanceEvent.TIME_SHIFT:
        current_step += event.event_value

    return absolute_time_sequence

  class AbsoluteTimeOneHotEncoding(encoder_decoder.OneHotEncoding):
    """One-hot encoding for performance note density events.
    Encodes by quantizing note density events. When decoding, always decodes to
    the minimum value for each bin. The first bin starts at zero note density.
    """

    def __init__(self, time_embbeding_bin):
      """Initialize a NoteDensityOneHotEncoding.
      Args:
        density_bin_ranges: List of note density (notes per second) bin
            boundaries to use when quantizing. The number of bins will be one
            larger than the list length.
      """
      self._time_embbeding_bin=time_embbeding_bin

    @property
    def num_classes(self):
      return self._time_embbeding_bin

    @property
    def default_event(self):
      return 0.0

    def encode_event(self, event):
      return math.floor(event * self._time_embbeding_bin)

    def decode_event(self, index):
      return index / self._time_embbeding_bin

class RelativeTimePerformanceControlSignal(PerformanceControlSignal):
  """Time embbeding performance control signal."""

  name = 'notes_per_second'
  description = 'Desired number of notes per second.'

  def __init__(self,time_embbeding_bin):
    """Initialize a NoteDensityPerformanceControlSignal.
    Args:
      window_size_seconds: The size of the window, in seconds, used to compute
          note density (notes per second).
      density_bin_ranges: List of note density (notes per second) bin boundaries
          to use when quantizing. The number of bins will be one larger than the
          list length.
    """
    self._encoder = encoder_decoder.OneHotEventSequenceEncoderDecoder(
        self.RelativeTimeOneHotEncoding(time_embbeding_bin))

  def validate(self, value):
    return isinstance(value, numbers.Number) and value >= 0.0

  @property
  def encoder(self):
    return self._encoder

  def extract(self, performance):
    """Computes note density at every event in a performance.
    Args:
      performance: A Performance object for which to compute a note density
          sequence.
    Returns:
      A list of note densities of the same length as `performance`, with each
      entry equal to the note time step
    """
    assert (hasattr(performance,"start_time_offset") and hasattr(performance,"end_time")) ,"To use absolutely time embbeding, performance mast have start time offset and end time"
    steps_per_second = performance.steps_per_second
    current_step = performance.start_time_offset * steps_per_second
    end_step = (performance.end_time + 1) * steps_per_second

    absolute_time_sequence = []

    for event in performance:
      assert current_step < end_step, "end step mast be largest current_step"
      absolute_time_sequence.append(current_step/end_step)
      if event.event_type == PerformanceEvent.TIME_SHIFT:
        current_step += event.event_value

    return absolute_time_sequence

  class RelativeTimeOneHotEncoding(encoder_decoder.OneHotEncoding):
    """One-hot encoding for performance note density events.
    Encodes by quantizing note density events. When decoding, always decodes to
    the minimum value for each bin. The first bin starts at zero note density.
    """

    def __init__(self, time_embbeding_bin):
      """Initialize a NoteDensityOneHotEncoding.
      Args:
        density_bin_ranges: List of note density (notes per second) bin
            boundaries to use when quantizing. The number of bins will be one
            larger than the list length.
      """
      self._time_embbeding_bin=time_embbeding_bin

    @property
    def num_classes(self):
      return self._time_embbeding_bin

    @property
    def default_event(self):
      return 0.0

    def encode_event(self, event):
      return math.floor(event * self._time_embbeding_bin)

    def decode_event(self, index):
      return index / self._time_embbeding_bin


class GenerateRelativeTimePerformanceControlSignal(PerformanceControlSignal):
  """Time embbeding performance control signal."""

  name = 'notes_per_second'
  description = 'Desired number of notes per second.'

  def __init__(self,time_embbeding_bin,max_time):
    """Initialize a NoteDensityPerformanceControlSignal.
    Args:
      window_size_seconds: The size of the window, in seconds, used to compute
          note density (notes per second).
      density_bin_ranges: List of note density (notes per second) bin boundaries
          to use when quantizing. The number of bins will be one larger than the
          list length.
    """
    self._encoder = encoder_decoder.OneHotEventSequenceEncoderDecoder(
        self.GenerateRelativeTimeOneHotEncoding(time_embbeding_bin))
    self._max_time=max_time
  def validate(self, value):
    return isinstance(value, numbers.Number) and value >= 0.0

  @property
  def encoder(self):
    return self._encoder

  def extract(self, performance):
    """Computes note density at every event in a performance.
    Args:
      performance: A Performance object for which to compute a note density
          sequence.
    Returns:
      A list of note densities of the same length as `performance`, with each
      entry equal to the note time step
    """
    assert (hasattr(performance,"start_time_offset") and hasattr(performance,"end_time")) ,"To use absolutely time embbeding, performance mast have start time offset and end time"
    steps_per_second = performance.steps_per_second
    current_step = performance.start_time_offset * steps_per_second
    end_step = (self._max_time + 1) * steps_per_second

    absolute_time_sequence = []

    for event in performance:
      assert current_step < end_step, "end step mast be largest current_step"
      absolute_time_sequence.append(current_step/end_step)
      if event.event_type == PerformanceEvent.TIME_SHIFT:
        current_step += event.event_value

    return absolute_time_sequence

  class GenerateRelativeTimeOneHotEncoding(encoder_decoder.OneHotEncoding):
    """One-hot encoding for performance note density events.
    Encodes by quantizing note density events. When decoding, always decodes to
    the minimum value for each bin. The first bin starts at zero note density.
    """

    def __init__(self, time_embbeding_bin):
      """Initialize a NoteDensityOneHotEncoding.
      Args:
        density_bin_ranges: List of note density (notes per second) bin
            boundaries to use when quantizing. The number of bins will be one
            larger than the list length.
      """
      self._time_embbeding_bin=time_embbeding_bin

    @property
    def num_classes(self):
      return self._time_embbeding_bin

    @property
    def default_event(self):
      return 0.0

    def encode_event(self, event):
      return math.floor(event * self._time_embbeding_bin)

    def decode_event(self, index):
      return index / self._time_embbeding_bin
