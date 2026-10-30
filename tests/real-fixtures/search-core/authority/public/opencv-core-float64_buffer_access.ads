--  Zero-copy, callback-scoped access to the complete element buffer of a
--  continuous single-channel Float64 (CV_64FC1) Mat of any dimension count.
--  The view aliases native storage and is valid only during the callback.
--  Every operation validates the Mat's depth, channel count and continuity
--  and raises OpenCV_Error on any mismatch, before the callback is invoked.

package OpenCV.Core.Float64_Buffer_Access is

   --  The flat element buffer of a Mat: one Float64_Value per Mat element, in
   --  OpenCV element order with the final dimension varying fastest. The
   --  callbacks pass arrays whose bounds are 0 .. Natural (Image.Total) - 1.
   type Buffer_Array is array (Natural range <>) of Float64_Value;

   --  Invokes Process with a zero-copy view of a continuous Float64 C1
   --  Mat of any dimension count; genuine N-D Mats are supported.
   --  Data directly aliases native OpenCV storage for the entire
   --  logical buffer; no pixel values are copied. The explicitly
   --  aliased callback formal guarantees that Data is passed by
   --  reference and directly denotes the borrowed Mat for the duration
   --  of Process. The ordinary lifetime of the view is the callback.
   --  Data is one flat zero-based array of Mat elements in OpenCV
   --  element order, final dimension varying fastest:
   --  Data'First = 0, Data'Last = Natural (Image.Total) - 1, and
   --  Data'Length = Natural (Image.Total). For Shape (D1, ..., Dn),
   --  zero-based index (I1, ..., In) is Data offset
   --  ((I1 * D2 + I2) * D3 + ...) * Dn + In. For a 2-D Mat, element
   --  Data (Row * Image.Columns + Column) denotes Image (Row, Column).
   --  There are no row separators, padding, or gaps. Image must be
   --  continuous (Is_Continuous); a nonempty non-continuous Mat, such
   --  as a gapped Region or Slice, raises OpenCV_Error before Process
   --  is invoked. A continuous Region or N-D Slice is accepted even
   --  when it is a submatrix. The implementation holds one shallow Mat
   --  lease for the callback so referenced storage cannot disappear
   --  merely because another header is rebound or finalized. That lease
   --  is deterministic memory management, not thread synchronization.
   --  Do not retain a reference or address of Data after Process
   --  returns. Read-only access performs no copy; if another alias
   --  mutates the shared storage during the callback, Data observes
   --  those changes according to ordinary aliasing rules.
   --  An empty Mat is accepted, and Process then receives an empty Data.
   --  @param Image A continuous Float64 Mat with exactly one channel.
   --  @param Process Callback that receives the borrowed buffer. Data is
   --  valid only during the call and must not be retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when Image
   --  is not a Float64 single-channel Mat or is nonempty and not continuous,
   --  or has more elements than Natural'Last.
   procedure With_Read_Only_Buffer
     (Image   : Mat;
      Process : not null access procedure (Data : aliased Buffer_Array));

   --  As With_Read_Only_Buffer, except Process receives an in-out view.
   --  Writes through Data mutate the actual Mat storage immediately.
   --  There is no write-back phase. A write through Data is visible
   --  through Image and any shallow alias before Process returns, and
   --  a write through another alias is immediately visible through
   --  Data. Exceptions raised by Process propagate unchanged; any
   --  writes completed before the exception remain visible.
   --  @param Image A continuous Float64 Mat with exactly one channel.
   --  @param Process Callback that receives the borrowed buffer for reading
   --  and writing. Data is valid only during the call and must not be
   --  retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when Image
   --  is not a Float64 single-channel Mat or is nonempty and not continuous,
   --  or has more elements than Natural'Last.
   procedure With_Writable_Buffer
     (Image   : in out Mat;
      Process :
        not null access procedure (Data : aliased in out Buffer_Array));

end OpenCV.Core.Float64_Buffer_Access;
