with OpenCV.Core.Int8_Vec3;

--  Row access for two-dimensional Int8 C3 (CV_8SC3) Mats. Each Row_Array
--  element is one complete 3-byte C3 element: Data (Column) (0 .. 2) are the
--  three native signed channels (-128 .. 127, OpenCV schar storage). No
--  color meaning is assigned to the channels.
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

package OpenCV.Core.Int8_Vec3_Row_Access is

   --  The values of one Mat row, one complete three-channel vector per
   --  column.
   type Row_Array is array (Natural range <>) of Int8_Vec3.Vector;

   --  Copies one row of Image into Data. Data'Length must equal
   --  Image.Columns; Data (Data'First) receives column 0. Image is unchanged
   --  and Data owns its values.
   --  @param Image A two-dimensional Int8 Mat with exactly three channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Data Receives one three-channel vector per column.
   --  @exception OpenCV_Error Raised when Image is not an Int8 three-channel
   --  Mat, Row is outside the Mat, or Data'Length differs from
   --  Image.Columns.
   --  Also raised when Data'Length exceeds Natural'Last / 3: copied rows
   --  use an intermediate buffer of three scalar channels per vector.
   --  This limit does not apply to the zero-copy row callbacks.
   procedure Read_Row (Image : Mat; Row : Natural; Data : out Row_Array);

   --  Copies Data into one row of Image. Data'Length must equal
   --  Image.Columns; Data (Data'First) is stored in column 0. The values are
   --  written to the Mat's actual storage, so shallow aliases and the parent
   --  of a Region observe them.
   --  @param Image A two-dimensional Int8 Mat with exactly three channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Data One three-channel vector per column.
   --  @exception OpenCV_Error Raised when Image is not an Int8 three-channel
   --  Mat, Row is outside the Mat, or Data'Length differs from
   --  Image.Columns.
   --  Also raised when Data'Length exceeds Natural'Last / 3: copied rows
   --  use an intermediate buffer of three scalar channels per vector.
   --  This limit does not apply to the zero-copy row callbacks.
   procedure Write_Row (Image : in out Mat; Row : Natural; Data : Row_Array);

   --  Invokes Process with a zero-copy view of one row. Data aliases the
   --  native row and is zero-based with Data'Length = Image.Columns.
   --  @param Image A two-dimensional Int8 Mat with exactly three channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Process Callback that receives the borrowed row. Data is valid
   --  only during the call and must not be retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when Image
   --  is not a two-dimensional Int8 three-channel Mat or Row is outside the
   --  Mat.
   procedure With_Read_Only_Row
     (Image   : Mat;
      Row     : Natural;
      Process : not null access procedure (Data : aliased Row_Array));

   --  As With_Read_Only_Row, except Process receives an in-out view whose
   --  writes mutate the Mat storage immediately.
   --  @param Image A two-dimensional Int8 Mat with exactly three channels.
   --  @param Row Zero-based row, in 0 .. Image.Rows - 1.
   --  @param Process Callback that receives the borrowed row for reading and
   --  writing. Data is valid only during the call and must not be retained.
   --  @exception OpenCV_Error Raised, before Process is invoked, when Image
   --  is not a two-dimensional Int8 three-channel Mat or Row is outside the
   --  Mat.
   procedure With_Writable_Row
     (Image   : in out Mat;
      Row     : Natural;
      Process : not null access procedure (Data : aliased in out Row_Array));

end OpenCV.Core.Int8_Vec3_Row_Access;
