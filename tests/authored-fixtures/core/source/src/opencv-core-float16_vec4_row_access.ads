with OpenCV.Core.Float16_Vec4;

--  Row access for two-dimensional Float16 C4 (CV_16FC4) Mats. Each Row_Array
--  element is one complete 8-byte C4 element: Data (Column) (0 .. 3) are the
--  four native Float16 channels, each the exact stored IEEE-754 binary16
--  encoding (signed zeros, subnormals, infinities and NaN payloads are never
--  converted or canonicalized).
--
--  Read_Row / Write_Row copy one complete row; Data'Length must equal
--  Image.Columns and Data'First may be any Natural.
--
--  With_Read_Only_Row / With_Writable_Row invoke Process with a zero-copy
--  view that directly aliases the native row for the duration of the
--  callback: Data'First = 0 and Data'Length = Image.Columns. Non-contiguous
--  Regions are supported. A shallow Mat lease keeps the storage alive even
--  if Image (or a parent Mat) is rebound during Process; the lease is memory
--  management, not synchronization. Writes are immediate; exceptions raised
--  by Process propagate and completed writes remain visible. Do not retain
--  a reference or address of Data after Process returns.

package OpenCV.Core.Float16_Vec4_Row_Access is

   --  The pixels of one Mat row, one Vector (four interleaved channel
   --  values) per column. Array bounds are the caller's choice: only the
   --  length matters, and the first array element always corresponds to
   --  column 0.
   type Row_Array is array (Natural range <>) of Float16_Vec4.Vector;

   --  Copies one row of Image into Data, keeping the exact binary16 bits of
   --  every channel. Data'Length must equal Image.Columns. Image is
   --  unchanged and Data owns its values.
   --  @param Image A two-dimensional Float16 Mat with exactly four channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Data Receives one four-channel pixel per column.
   --  @exception OpenCV_Error Raised when Image is not a Float16 four-channel
   --  two-dimensional Mat, Row is outside the Mat, or Data'Length differs
   --  from Image.Columns.
   procedure Read_Row (Image : Mat; Row : Natural; Data : out Row_Array);

   --  Copies Data into one row of Image, keeping the exact binary16 bits of
   --  every channel. Data'Length must equal Image.Columns. The values are
   --  written to the Mat's actual storage, so shallow aliases and the parent
   --  of a Region observe them.
   --  @param Image A two-dimensional Float16 Mat with exactly four channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Data One four-channel pixel per column.
   --  @exception OpenCV_Error Raised when Image is not a Float16 four-channel
   --  two-dimensional Mat, Row is outside the Mat, or Data'Length differs
   --  from Image.Columns.
   procedure Write_Row (Image : in out Mat; Row : Natural; Data : Row_Array);

   --  Invokes Process with a zero-copy view of one Float16 C4 Mat row. Data
   --  aliases the native storage of that row; no pixel values are copied.
   --  Only the active row elements are exposed, never inter-row padding.
   --  @param Image A two-dimensional Float16 Mat with exactly four channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Process Callback that receives the borrowed row. Data is valid
   --  only during the call and must not be retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when Image
   --  is not a two-dimensional Float16 four-channel Mat or Row is outside the
   --  Mat.
   procedure With_Read_Only_Row
     (Image   : Mat;
      Row     : Natural;
      Process : not null access procedure (Data : aliased Row_Array));

   --  As With_Read_Only_Row, except Process receives an in-out view. Writes
   --  through Data mutate the actual Mat storage immediately.
   --  @param Image A two-dimensional Float16 Mat with exactly four channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Process Callback that receives the borrowed row for reading and
   --  writing. Data is valid only during the call and must not be retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when Image
   --  is not a two-dimensional Float16 four-channel Mat or Row is outside the
   --  Mat.
   procedure With_Writable_Row
     (Image   : in out Mat;
      Row     : Natural;
      Process : not null access procedure (Data : aliased in out Row_Array));
end OpenCV.Core.Float16_Vec4_Row_Access;
