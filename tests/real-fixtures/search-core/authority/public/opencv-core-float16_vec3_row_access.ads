with OpenCV.Core.Float16_Vec3;

--  Whole-row access to three-channel Float16 (CV_16FC3) two-dimensional
--  Mats, by copy (Read_Row, Write_Row) or by a zero-copy callback-scoped view
--  (With_Read_Only_Row, With_Writable_Row). Each element is one complete
--  three-channel pixel, a Float16_Vec3.Vector, whose components are the exact
--  stored IEEE-754 binary16 encodings. Row and column indices are
--  zero-based. Every operation validates the Mat's depth, channel count, row
--  index and row length and raises OpenCV_Error on any mismatch.

package OpenCV.Core.Float16_Vec3_Row_Access is

   --  Zero-based column position within a row.
   subtype Column_Index is Natural;

   --  The pixels of one Mat row, one Vector (three interleaved channel
   --  values) per column. Array bounds are the caller's choice: only the
   --  length matters, and the first array element always corresponds to
   --  column 0. The zero-copy callbacks pass arrays whose bounds are
   --  0 .. Image.Columns - 1.
   type Row_Array is
     array (Natural range <>) of OpenCV.Core.Float16_Vec3.Vector;

   --  Copies one row of Image into Data, keeping the exact binary16 bits of
   --  every channel. Data'Length must equal Image.Columns; Data (Data'First)
   --  receives column 0 and the array's index bounds are otherwise
   --  irrelevant. Image is unchanged, Data owns its values, and
   --  non-contiguous Regions are supported.
   --  @param Image A two-dimensional Float16 Mat with exactly three
   --  channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Data Receives one three-channel pixel per column.
   --  @exception OpenCV_Error Raised when Image is not a Float16
   --  three-channel two-dimensional Mat, Row is outside the Mat, or
   --  Data'Length differs from Image.Columns.
   --  Also raised when Data'Length exceeds Natural'Last / 3: copied rows
   --  use an intermediate buffer of three scalar channels per vector.
   --  This limit does not apply to the zero-copy row callbacks.
   procedure Read_Row (Image : Mat; Row : Natural; Data : out Row_Array);

   --  Copies Data into one row of Image, keeping the exact binary16 bits of
   --  every channel. Data'Length must equal Image.Columns; Data (Data'First)
   --  is stored in column 0. The values are written to the Mat's actual
   --  storage, so shallow aliases and the parent of a Region observe them.
   --  Non-contiguous Regions are supported.
   --  @param Image A two-dimensional Float16 Mat with exactly three
   --  channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Data One three-channel pixel per column.
   --  @exception OpenCV_Error Raised when Image is not a Float16
   --  three-channel two-dimensional Mat, Row is outside the Mat, or
   --  Data'Length differs from Image.Columns.
   --  Also raised when Data'Length exceeds Natural'Last / 3: copied rows
   --  use an intermediate buffer of three scalar channels per vector.
   --  This limit does not apply to the zero-copy row callbacks.
   procedure Write_Row (Image : in out Mat; Row : Natural; Data : Row_Array);

   --  Invokes Process with a zero-copy view of one Float16 C3 Mat row.
   --  Data directly aliases native OpenCV storage for that logical row;
   --  no pixel values are copied. Each Data element is one complete
   --  interleaved C3 pixel: Data (Column) (0 .. 2) are the three native
   --  Float16 channels. Each component is the exact stored IEEE-754
   --  binary16 encoding; signed zeros, subnormals, infinities, and NaN
   --  payloads are not converted or canonicalized. The explicitly
   --  aliased callback formal guarantees that Data is passed by
   --  reference and directly denotes the borrowed Mat row for the
   --  duration of Process. The ordinary lifetime of the view is the
   --  callback. Data is indexed with zero-based Mat columns:
   --  Data'First = 0, Data'Last = Image.Columns - 1, and Data'Length =
   --  Image.Columns. Only the active row elements are exposed, never
   --  inter-row padding. Non-contiguous Regions are supported because
   --  each 2-D logical row remains a contiguous sequence even when the
   --  parent stride is larger. The implementation holds a shallow Mat
   --  lease for the callback so referenced storage cannot disappear
   --  merely because another header is rebound or finalized. That lease
   --  is deterministic memory management, not thread synchronization.
   --  Do not retain a reference or address of Data after Process
   --  returns. Read-only access performs no copy; if another alias
   --  mutates the shared storage during the callback, Data observes
   --  those changes according to ordinary aliasing rules.
   --  Image.Is_Continuous is not required.
   --  @param Image A two-dimensional Float16 Mat with exactly three
   --  channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Process Callback that receives the borrowed row. Data is valid
   --  only during the call and must not be retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when Image
   --  is not a two-dimensional Float16 three-channel Mat or Row is outside
   --  the Mat.
   procedure With_Read_Only_Row
     (Image   : Mat;
      Row     : Natural;
      Process : not null access procedure (Data : aliased Row_Array));

   --  As With_Read_Only_Row, except Process receives an in-out view.
   --  Writes through Data mutate the actual Mat storage immediately.
   --  There is no write-back phase. A write through Data is visible
   --  through Image and any shallow alias before Process returns, and
   --  a write through another alias is immediately visible through
   --  Data. Exceptions raised by Process propagate unchanged; any
   --  writes completed before the exception remain visible.
   --  @param Image A two-dimensional Float16 Mat with exactly three
   --  channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Process Callback that receives the borrowed row for reading and
   --  writing. Data is valid only during the call and must not be retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when Image
   --  is not a two-dimensional Float16 three-channel Mat or Row is outside
   --  the Mat.
   procedure With_Writable_Row
     (Image   : in out Mat;
      Row     : Natural;
      Process : not null access procedure (Data : aliased in out Row_Array));

end OpenCV.Core.Float16_Vec3_Row_Access;
