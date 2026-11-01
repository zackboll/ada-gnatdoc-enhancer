with Interfaces;
with Interfaces.C;
with System;

package OpenCV.Internal.C_API is

   type Status is new Interfaces.Integer_32;

   Success                : constant Status := 0;
   Error_OpenCV           : constant Status := 1;
   Error_Standard_CPP     : constant Status := 2;
   Error_Unknown          : constant Status := 3;
   Error_Invalid_Argument : constant Status := 4;

   type Mat_Handle is new System.Address;
   Null_Mat_Handle : constant Mat_Handle := Mat_Handle (System.Null_Address);

   subtype C_Int32 is Interfaces.Integer_32;
   subtype C_UInt8 is Interfaces.Unsigned_8;
   subtype C_Int8 is Interfaces.Integer_8;
   subtype C_UInt16 is Interfaces.Unsigned_16;
   subtype C_Int16 is Interfaces.Integer_16;
   subtype C_UInt32 is Interfaces.Unsigned_32;
   subtype C_UInt64 is Interfaces.Unsigned_64;
   subtype C_Float32 is Interfaces.C.C_float;
   subtype C_Float64 is Interfaces.IEEE_Float_64;
   subtype C_Double is Interfaces.C.double;

   function Native_Version_String
     (Buffer            : System.Address;
      Capacity          : C_UInt64;
      Required, Written : access C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_native_version_string";

   function Native_Build_Information
     (Buffer            : System.Address;
      Capacity          : C_UInt64;
      Required, Written : access C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_native_build_information";

   type UMat_Handle is new System.Address;
   Null_UMat_Handle : constant UMat_Handle :=
     UMat_Handle (System.Null_Address);

   function UMat_Create (Result : access UMat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_umat_create";
   function UMat_Create_2D
     (Rows, Columns, Depth, Channels : C_Int32; Result : access UMat_Handle)
      return Status
   with Import, Convention => C, External_Name => "opencv_core_umat_create_2d";
   function UMat_Create_ND
     (Dims            : C_Int32;
      Sizes           : access constant C_Int32;
      Depth, Channels : C_Int32;
      Result          : access UMat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_umat_create_nd";
   function UMat_Copy
     (Source : UMat_Handle; Result : access UMat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_umat_copy";
   function UMat_Clone
     (Source : UMat_Handle; Result : access UMat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_umat_clone";
   procedure UMat_Destroy (Self : UMat_Handle)
   with Import, Convention => C, External_Name => "opencv_core_umat_destroy";
   function Mat_To_UMat
     (Source : Mat_Handle; Result : access UMat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_to_umat";
   function UMat_To_Mat
     (Source : UMat_Handle; Result : access Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_umat_to_mat";
   function UMat_Copy_To
     (Source : UMat_Handle; Result : access UMat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_umat_copy_to";
   function UMat_Convert_To
     (Source        : UMat_Handle;
      Depth         : C_Int32;
      Scale, Offset : C_Double;
      Result        : access UMat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_convert_to";
   function UMat_Convert_To_Into
     (Source, Destination : UMat_Handle;
      Depth               : C_Int32;
      Scale, Offset       : C_Double) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_convert_to_into";
   function UMat_Region
     (Source              : UMat_Handle;
      X, Y, Width, Height : C_Int32;
      Result              : access UMat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_umat_region";
   function UMat_Locate_ROI
     (Source                                        : UMat_Handle;
      Whole_Width, Whole_Height, Offset_X, Offset_Y : access C_Int32)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_locate_roi";
   function UMat_Adjust_ROI
     (Self : UMat_Handle; Top, Bottom, Left, Right : C_Int32) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_adjust_roi";
   function UMat_Slice_ND
     (Source        : UMat_Handle;
      Dims          : C_Int32;
      Starts, Stops : access constant C_Int32;
      Result        : access UMat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_umat_slice_nd";
   function UMat_Is_Empty
     (Self : UMat_Handle; Result : access C_UInt8) return Status
   with Import, Convention => C, External_Name => "opencv_core_umat_is_empty";
   function UMat_Is_Continuous
     (Self : UMat_Handle; Result : access C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_is_continuous";
   function UMat_Is_Submatrix
     (Self : UMat_Handle; Result : access C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_is_submatrix";
   function UMat_Dimension_Count
     (Self : UMat_Handle; Result : access C_Int32) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_dimension_count";
   function UMat_Extent
     (Self : UMat_Handle; Axis : C_Int32; Result : access C_Int32)
      return Status
   with Import, Convention => C, External_Name => "opencv_core_umat_extent";
   function UMat_Rows
     (Self : UMat_Handle; Result : access C_Int32) return Status
   with Import, Convention => C, External_Name => "opencv_core_umat_rows";
   function UMat_Columns
     (Self : UMat_Handle; Result : access C_Int32) return Status
   with Import, Convention => C, External_Name => "opencv_core_umat_columns";
   function UMat_Depth
     (Self : UMat_Handle; Result : access C_Int32) return Status
   with Import, Convention => C, External_Name => "opencv_core_umat_depth";
   function UMat_Channels
     (Self : UMat_Handle; Result : access C_Int32) return Status
   with Import, Convention => C, External_Name => "opencv_core_umat_channels";
   function UMat_Total
     (Self : UMat_Handle; Result : access C_UInt64) return Status
   with Import, Convention => C, External_Name => "opencv_core_umat_total";
   function UMat_Element_Size
     (Self : UMat_Handle; Result : access C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_element_size";
   function UMat_Channel_Size
     (Self : UMat_Handle; Result : access C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_channel_size";

   type Sparse_Mat_Handle is new System.Address;
   Null_Sparse_Mat_Handle      : constant Sparse_Mat_Handle :=
     Sparse_Mat_Handle (System.Null_Address);
   type Sparse_Iterator_Handle is new System.Address;
   Null_Sparse_Iterator_Handle : constant Sparse_Iterator_Handle :=
     Sparse_Iterator_Handle (System.Null_Address);

   type File_Storage_Handle is new System.Address;
   Null_File_Storage_Handle : constant File_Storage_Handle :=
     File_Storage_Handle (System.Null_Address);

   type Mat_Handle_Array is array (Natural range <>) of aliased Mat_Handle
   with Convention => C;

   type C_Int32_Array is array (Natural range <>) of aliased C_Int32
   with Convention => C;

   subtype Sparse_C_UInt64 is Interfaces.Unsigned_64;

   function Sparse_Iterator_Create
     (Source : Sparse_Mat_Handle; Result : access Sparse_Iterator_Handle)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_const_iterator_create";
   procedure Sparse_Iterator_Destroy (Self : Sparse_Iterator_Handle)
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_const_iterator_destroy";
   function Sparse_Iterator_Next_UInt8
     (Self    : Sparse_Iterator_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access C_UInt8;
      Found   : access C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_const_iterator_next_uint8";
   function Sparse_Iterator_Next_Int8
     (Self    : Sparse_Iterator_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access C_Int8;
      Found   : access C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_const_iterator_next_int8";
   function Sparse_Iterator_Next_UInt16
     (Self    : Sparse_Iterator_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access C_UInt16;
      Found   : access C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_const_iterator_next_uint16";
   function Sparse_Iterator_Next_Int16
     (Self    : Sparse_Iterator_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access C_Int16;
      Found   : access C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_const_iterator_next_int16";
   function Sparse_Iterator_Next_Int32
     (Self    : Sparse_Iterator_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access C_Int32;
      Found   : access C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_const_iterator_next_int32";
   function Sparse_Iterator_Next_Float16
     (Self    : Sparse_Iterator_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access C_UInt16;
      Found   : access C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_const_iterator_next_float16";
   function Sparse_Iterator_Next_Float32
     (Self    : Sparse_Iterator_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access C_Float32;
      Found   : access C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_const_iterator_next_float32";
   function Sparse_Iterator_Next_Float64
     (Self    : Sparse_Iterator_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access C_Float64;
      Found   : access C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_const_iterator_next_float64";

   function Sparse_Create (Result : access Sparse_Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_sparse_create";
   function Sparse_Create_ND
     (Dims            : C_Int32;
      Sizes           : access C_Int32;
      Depth, Channels : C_Int32;
      Result          : access Sparse_Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_create_nd";
   function Sparse_From_Dense
     (Source : Mat_Handle; Result : access Sparse_Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_from_dense";
   function Sparse_To_Dense
     (Source : Sparse_Mat_Handle; Result : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_to_dense";
   function Sparse_Convert_To_Sparse
     (Source       : Sparse_Mat_Handle;
      Output_Depth : C_Int32;
      Scale        : C_Float64;
      Result       : access Sparse_Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_convert_to_sparse";
   function Sparse_Convert_To_Dense
     (Source       : Sparse_Mat_Handle;
      Output_Depth : C_Int32;
      Scale        : C_Float64;
      Offset       : C_Float64;
      Result       : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_convert_to_dense";
   function Sparse_Norm
     (Source : Sparse_Mat_Handle; Kind : C_Int32; Result : access C_Float64)
      return Status
   with Import, Convention => C, External_Name => "opencv_core_sparse_norm";
   function Sparse_Normalize
     (Source      : Sparse_Mat_Handle;
      Target_Norm : C_Float64;
      Kind        : C_Int32;
      Result      : access Sparse_Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_normalize";
   function Sparse_Min_Max_Loc
     (Source          : Sparse_Mat_Handle;
      Minimum         : access C_Float64;
      Maximum         : access C_Float64;
      Minimum_Indices : access C_Int32;
      Maximum_Indices : access C_Int32;
      Index_Count     : C_Int32;
      Has_Minimum     : access C_UInt8;
      Has_Maximum     : access C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_min_max_loc";
   function Sparse_Copy
     (Source : Sparse_Mat_Handle; Result : access Sparse_Mat_Handle)
      return Status
   with Import, Convention => C, External_Name => "opencv_core_sparse_copy";
   function Sparse_Clone
     (Source : Sparse_Mat_Handle; Result : access Sparse_Mat_Handle)
      return Status
   with Import, Convention => C, External_Name => "opencv_core_sparse_clone";
   procedure Sparse_Destroy (Self : Sparse_Mat_Handle)
   with Import, Convention => C, External_Name => "opencv_core_sparse_destroy";
   function Sparse_Clear (Self : Sparse_Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_sparse_clear";
   function Sparse_Metadata
     (Self                                : Sparse_Mat_Handle;
      Dims, Depth, Channels               : access C_Int32;
      Element_Bytes, Channel_Bytes, Nodes : access Sparse_C_UInt64)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_metadata";
   function Sparse_Extent
     (Self : Sparse_Mat_Handle; Axis : C_Int32; Value : access C_Int32)
      return Status
   with Import, Convention => C, External_Name => "opencv_core_sparse_extent";
   function Sparse_Contains
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Found   : access C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_contains";
   function Sparse_Erase
     (Self : Sparse_Mat_Handle; Dims : C_Int32; Indices : access C_Int32)
      return Status
   with Import, Convention => C, External_Name => "opencv_core_sparse_erase";

   function Sparse_Get_UInt8
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_get_uint8";
   function Sparse_Set_UInt8
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_set_uint8";
   function Sparse_Get_Int8
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access C_Int8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_get_int8";
   function Sparse_Set_Int8
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : C_Int8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_set_int8";
   function Sparse_Get_UInt16
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access C_UInt16) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_get_uint16";
   function Sparse_Set_UInt16
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : C_UInt16) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_set_uint16";
   function Sparse_Get_Int16
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access C_Int16) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_get_int16";
   function Sparse_Set_Int16
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : C_Int16) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_set_int16";
   function Sparse_Get_Int32
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access C_Int32) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_get_int32";
   function Sparse_Set_Int32
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : C_Int32) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_set_int32";
   function Sparse_Get_Float16
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access C_UInt16) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_get_float16";
   function Sparse_Set_Float16
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : C_UInt16) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_set_float16";
   function Sparse_Get_Float32
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access C_Float32) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_get_float32";
   function Sparse_Set_Float32
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : C_Float32) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_set_float32";
   function Sparse_Get_Float64
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access C_Float64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_get_float64";
   function Sparse_Set_Float64
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : C_Float64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_set_float64";

   type C_UInt8_Array is array (Natural range <>) of aliased C_UInt8
   with Convention => C;

   type C_UInt64_Array is array (Natural range <>) of aliased C_UInt64
   with Convention => C;

   type Scalar is record
      Component_0 : C_Double;
      Component_1 : C_Double;
      Component_2 : C_Double;
      Component_3 : C_Double;
   end record
   with Convention => C;

   type Point is record
      X : C_Int32;
      Y : C_Int32;
   end record
   with Convention => C;

   type Point_Array is array (Natural range <>) of aliased Point
   with Convention => C;

   type UInt8_Vec3 is record
      Component_0 : C_UInt8;
      Component_1 : C_UInt8;
      Component_2 : C_UInt8;
   end record
   with Convention => C;

   type Float32_Vec3 is record
      Component_0 : C_Float32;
      Component_1 : C_Float32;
      Component_2 : C_Float32;
   end record
   with Convention => C;

   type Float64_Vec3 is record
      Component_0 : C_Float64;
      Component_1 : C_Float64;
      Component_2 : C_Float64;
   end record
   with Convention => C;
   pragma
     Compile_Time_Error (Float64_Vec3'Size /= 192, "C Vec3 size mismatch");

   type UInt8_Vec4 is record
      Component_0, Component_1, Component_2, Component_3 : C_UInt8;
   end record
   with Convention => C;
   pragma
     Compile_Time_Error (UInt8_Vec4'Size /= 32, "C UInt8 Vec4 size mismatch");

   type UInt16_Vec4 is record
      Component_0, Component_1, Component_2, Component_3 : C_UInt16;
   end record
   with Convention => C;
   pragma
     Compile_Time_Error
       (UInt16_Vec4'Size /= 64, "C UInt16 Vec4 size mismatch");

   type Float32_Vec4 is record
      Component_0, Component_1, Component_2, Component_3 : C_Float32;
   end record
   with Convention => C;
   type Float64_Vec4 is record
      Component_0, Component_1, Component_2, Component_3 : C_Float64;
   end record
   with Convention => C;
   pragma
     Compile_Time_Error
       (Float32_Vec4'Size /= 128, "C Float32 Vec4 size mismatch");
   pragma
     Compile_Time_Error
       (Float64_Vec4'Size /= 256, "C Float64 Vec4 size mismatch");

   type Float32_Vec2 is record
      Component_0 : C_Float32;
      Component_1 : C_Float32;
   end record
   with Convention => C;

   type UInt8_Vec2 is record
      Component_0, Component_1 : C_UInt8;
   end record
   with Convention => C;
   pragma
     Compile_Time_Error (UInt8_Vec2'Size /= 16, "C UInt8 Vec2 size mismatch");

   type UInt16_Vec2 is record
      Component_0, Component_1 : C_UInt16;
   end record
   with Convention => C;
   pragma
     Compile_Time_Error
       (UInt16_Vec2'Size /= 32, "C UInt16 Vec2 size mismatch");

   type Float64_Vec2 is record
      Component_0 : C_Float64;
      Component_1 : C_Float64;
   end record
   with Convention => C;

   pragma Compile_Time_Error (Float32_Vec2'Size /= 64, "C Vec2 size mismatch");
   pragma
     Compile_Time_Error (Float64_Vec2'Size /= 128, "C Vec2 size mismatch");
   --  Each component is the stored IEEE binary16 encoding, not an
   --  integer-valued channel.
   type Float16_Vec3 is record
      Component_0 : C_UInt16;
      Component_1 : C_UInt16;
      Component_2 : C_UInt16;
   end record
   with Convention => C;

   --  Raw binary16 encodings for one complete CV_16FC2 / CV_16FC4 element.
   --  Each component is the stored IEEE-754 binary16 bit pattern, not an
   --  integer-valued channel and not a numeric conversion result.
   type Float16_Vec2 is record
      Component_0, Component_1 : C_UInt16;
   end record
   with Convention => C;
   pragma Compile_Time_Error (Float16_Vec2'Size /= 32, "C Float16 Vec2 size");

   type Float16_Vec4 is record
      Component_0, Component_1, Component_2, Component_3 : C_UInt16;
   end record
   with Convention => C;
   pragma Compile_Time_Error (Float16_Vec4'Size /= 64, "C Float16 Vec4 size");

   function Mat_Get_Float16_Vec2
     (Self : Mat_Handle; Row, Column : C_Int32; Result : access Float16_Vec2)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_float16_vec2";
   function Mat_Set_Float16_Vec2
     (Self        : Mat_Handle;
      Row, Column : C_Int32;
      Value       : access constant Float16_Vec2) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_float16_vec2";
   function Mat_Get_Float16_Vec2_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Result          : access Float16_Vec2) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_float16_vec2_nd";
   function Mat_Set_Float16_Vec2_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Value           : access constant Float16_Vec2) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_float16_vec2_nd";
   --  Data carries two uint16_t binary16 encodings per element.
   function Mat_Read_Float16_Vec2_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_read_float16_vec2_row";
   function Mat_Write_Float16_Vec2_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_write_float16_vec2_row";

   function Mat_Get_Float16_Vec4
     (Self : Mat_Handle; Row, Column : C_Int32; Result : access Float16_Vec4)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_float16_vec4";
   function Mat_Set_Float16_Vec4
     (Self        : Mat_Handle;
      Row, Column : C_Int32;
      Value       : access constant Float16_Vec4) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_float16_vec4";
   function Mat_Get_Float16_Vec4_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Result          : access Float16_Vec4) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_float16_vec4_nd";
   function Mat_Set_Float16_Vec4_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Value           : access constant Float16_Vec4) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_float16_vec4_nd";
   --  Data carries four uint16_t binary16 encodings per element.
   function Mat_Read_Float16_Vec4_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_read_float16_vec4_row";
   function Mat_Write_Float16_Vec4_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_write_float16_vec4_row";

   type UInt16_Vec3 is record
      Component_0 : C_UInt16;
      Component_1 : C_UInt16;
      Component_2 : C_UInt16;
   end record
   with Convention => C;
   pragma
     Compile_Time_Error
       (UInt16_Vec3'Size /= 48, "C UInt16 Vec3 size mismatch");

   type Int16_Vec2 is record
      Component_0, Component_1 : C_Int16;
   end record
   with Convention => C;
   pragma Compile_Time_Error (Int16_Vec2'Size /= 32, "C Int16 Vec2 size");

   type Int16_Vec3 is record
      Component_0, Component_1, Component_2 : C_Int16;
   end record
   with Convention => C;
   pragma Compile_Time_Error (Int16_Vec3'Size /= 48, "C Int16 Vec3 size");

   type Int16_Vec4 is record
      Component_0, Component_1, Component_2, Component_3 : C_Int16;
   end record
   with Convention => C;
   pragma Compile_Time_Error (Int16_Vec4'Size /= 64, "C Int16 Vec4 size");

   type Int32_Vec2 is record
      Component_0, Component_1 : C_Int32;
   end record
   with Convention => C;
   pragma Compile_Time_Error (Int32_Vec2'Size /= 64, "C Int32 Vec2 size");
   type Int32_Vec3 is record
      Component_0, Component_1, Component_2 : C_Int32;
   end record
   with Convention => C;
   pragma Compile_Time_Error (Int32_Vec3'Size /= 96, "C Int32 Vec3 size");
   type Int32_Vec4 is record
      Component_0, Component_1, Component_2, Component_3 : C_Int32;
   end record
   with Convention => C;
   pragma Compile_Time_Error (Int32_Vec4'Size /= 128, "C Int32 Vec4 size");

   function Mat_Get_Int32_Vec2
     (Self : Mat_Handle; Row, Column : C_Int32; Result : access Int32_Vec2)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_int32_vec2";
   function Mat_Set_Int32_Vec2
     (Self        : Mat_Handle;
      Row, Column : C_Int32;
      Value       : access constant Int32_Vec2) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_int32_vec2";
   function Mat_Get_Int32_Vec2_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Result          : access Int32_Vec2) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_int32_vec2_nd";
   function Mat_Set_Int32_Vec2_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Value           : access constant Int32_Vec2) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_int32_vec2_nd";
   function Mat_Read_Int32_Vec2_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_read_int32_vec2_row";
   function Mat_Write_Int32_Vec2_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_write_int32_vec2_row";

   function Mat_Get_Int32_Vec3
     (Self : Mat_Handle; Row, Column : C_Int32; Result : access Int32_Vec3)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_int32_vec3";
   function Mat_Set_Int32_Vec3
     (Self        : Mat_Handle;
      Row, Column : C_Int32;
      Value       : access constant Int32_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_int32_vec3";
   function Mat_Get_Int32_Vec3_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Result          : access Int32_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_int32_vec3_nd";
   function Mat_Set_Int32_Vec3_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Value           : access constant Int32_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_int32_vec3_nd";
   function Mat_Read_Int32_Vec3_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_read_int32_vec3_row";
   function Mat_Write_Int32_Vec3_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_write_int32_vec3_row";

   function Mat_Get_Int32_Vec4
     (Self : Mat_Handle; Row, Column : C_Int32; Result : access Int32_Vec4)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_int32_vec4";
   function Mat_Set_Int32_Vec4
     (Self        : Mat_Handle;
      Row, Column : C_Int32;
      Value       : access constant Int32_Vec4) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_int32_vec4";
   function Mat_Get_Int32_Vec4_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Result          : access Int32_Vec4) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_int32_vec4_nd";
   function Mat_Set_Int32_Vec4_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Value           : access constant Int32_Vec4) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_int32_vec4_nd";
   function Mat_Read_Int32_Vec4_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_read_int32_vec4_row";
   function Mat_Write_Int32_Vec4_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_write_int32_vec4_row";

   --  Signed 8-bit complete CV_8SC2/C3/C4 elements. Components are C int8_t
   --  (OpenCV's native scalar is schar; the shim converts explicitly).
   --  Rows transfer flat C_Int8 scalars in channel order.
   pragma Compile_Time_Error (C_Int8'Size /= 8, "C Int8 scalar size");
   type Int8_Vec2 is record
      Component_0, Component_1 : C_Int8;
   end record
   with Convention => C;
   pragma Compile_Time_Error (Int8_Vec2'Size /= 16, "C Int8 Vec2 size");
   type Int8_Vec3 is record
      Component_0, Component_1, Component_2 : C_Int8;
   end record
   with Convention => C;
   pragma Compile_Time_Error (Int8_Vec3'Size /= 24, "C Int8 Vec3 size");
   type Int8_Vec4 is record
      Component_0, Component_1, Component_2, Component_3 : C_Int8;
   end record
   with Convention => C;
   pragma Compile_Time_Error (Int8_Vec4'Size /= 32, "C Int8 Vec4 size");

   function Mat_Get_Int8_Vec2
     (Self : Mat_Handle; Row, Column : C_Int32; Result : access Int8_Vec2)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_int8_vec2";
   function Mat_Set_Int8_Vec2
     (Self        : Mat_Handle;
      Row, Column : C_Int32;
      Value       : access constant Int8_Vec2) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_int8_vec2";
   function Mat_Get_Int8_Vec2_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Result          : access Int8_Vec2) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_int8_vec2_nd";
   function Mat_Set_Int8_Vec2_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Value           : access constant Int8_Vec2) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_int8_vec2_nd";
   function Mat_Read_Int8_Vec2_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_read_int8_vec2_row";
   function Mat_Write_Int8_Vec2_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_write_int8_vec2_row";

   function Mat_Get_Int8_Vec3
     (Self : Mat_Handle; Row, Column : C_Int32; Result : access Int8_Vec3)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_int8_vec3";
   function Mat_Set_Int8_Vec3
     (Self        : Mat_Handle;
      Row, Column : C_Int32;
      Value       : access constant Int8_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_int8_vec3";
   function Mat_Get_Int8_Vec3_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Result          : access Int8_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_int8_vec3_nd";
   function Mat_Set_Int8_Vec3_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Value           : access constant Int8_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_int8_vec3_nd";
   function Mat_Read_Int8_Vec3_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_read_int8_vec3_row";
   function Mat_Write_Int8_Vec3_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_write_int8_vec3_row";

   function Mat_Get_Int8_Vec4
     (Self : Mat_Handle; Row, Column : C_Int32; Result : access Int8_Vec4)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_int8_vec4";
   function Mat_Set_Int8_Vec4
     (Self        : Mat_Handle;
      Row, Column : C_Int32;
      Value       : access constant Int8_Vec4) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_int8_vec4";
   function Mat_Get_Int8_Vec4_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Result          : access Int8_Vec4) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_int8_vec4_nd";
   function Mat_Set_Int8_Vec4_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Value           : access constant Int8_Vec4) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_int8_vec4_nd";
   function Mat_Read_Int8_Vec4_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_read_int8_vec4_row";
   function Mat_Write_Int8_Vec4_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_write_int8_vec4_row";

   --  Signed complete-element access; rows transfer flat C_Int16 scalars.
   function Mat_Get_Int16_Vec2
     (Self : Mat_Handle; Row, Column : C_Int32; Result : access Int16_Vec2)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_int16_vec2";
   function Mat_Set_Int16_Vec2
     (Self        : Mat_Handle;
      Row, Column : C_Int32;
      Value       : access constant Int16_Vec2) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_int16_vec2";
   function Mat_Get_Int16_Vec2_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Result          : access Int16_Vec2) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_int16_vec2_nd";
   function Mat_Set_Int16_Vec2_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Value           : access constant Int16_Vec2) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_int16_vec2_nd";
   function Mat_Read_Int16_Vec2_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_read_int16_vec2_row";
   function Mat_Write_Int16_Vec2_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_write_int16_vec2_row";

   function Mat_Get_Int16_Vec3
     (Self : Mat_Handle; Row, Column : C_Int32; Result : access Int16_Vec3)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_int16_vec3";
   function Mat_Set_Int16_Vec3
     (Self        : Mat_Handle;
      Row, Column : C_Int32;
      Value       : access constant Int16_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_int16_vec3";
   function Mat_Get_Int16_Vec3_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Result          : access Int16_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_int16_vec3_nd";
   function Mat_Set_Int16_Vec3_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Value           : access constant Int16_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_int16_vec3_nd";
   function Mat_Read_Int16_Vec3_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_read_int16_vec3_row";
   function Mat_Write_Int16_Vec3_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_write_int16_vec3_row";

   function Mat_Get_Int16_Vec4
     (Self : Mat_Handle; Row, Column : C_Int32; Result : access Int16_Vec4)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_int16_vec4";
   function Mat_Set_Int16_Vec4
     (Self        : Mat_Handle;
      Row, Column : C_Int32;
      Value       : access constant Int16_Vec4) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_int16_vec4";
   function Mat_Get_Int16_Vec4_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Result          : access Int16_Vec4) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_int16_vec4_nd";
   function Mat_Set_Int16_Vec4_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Value           : access constant Int16_Vec4) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_int16_vec4_nd";
   function Mat_Read_Int16_Vec4_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_read_int16_vec4_row";
   function Mat_Write_Int16_Vec4_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_write_int16_vec4_row";

   Depth_UInt8   : constant C_Int32 := 0;
   Depth_Int8    : constant C_Int32 := 1;
   Depth_UInt16  : constant C_Int32 := 2;
   Depth_Int16   : constant C_Int32 := 3;
   Depth_Int32   : constant C_Int32 := 4;
   Depth_Float32 : constant C_Int32 := 5;
   Depth_Float64 : constant C_Int32 := 6;
   Depth_Float16 : constant C_Int32 := 7;

   LP_Unique         : constant C_Int32 := 0;
   LP_Multiple       : constant C_Int32 := 1;
   LP_Unbounded      : constant C_Int32 := 2;
   LP_Infeasible     : constant C_Int32 := 3;
   LP_Numerical_Loss : constant C_Int32 := 4;

   Norm_L1  : constant C_Int32 := 1;
   Norm_L2  : constant C_Int32 := 2;
   Norm_Inf : constant C_Int32 := 3;

   Normalize_L1      : constant C_Int32 := 1;
   Normalize_L2      : constant C_Int32 := 2;
   Normalize_Inf     : constant C_Int32 := 3;
   Normalize_Min_Max : constant C_Int32 := 4;

   function Mat_Storage_Relation
     (Source, Destination : Mat_Handle; Relation : access C_Int32)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_storage_relation";

   function Mat_Scalar_Arithmetic
     (Source    : Mat_Handle;
      Value     : access constant Scalar;
      Operation : C_Int32;
      Result    : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_scalar_arithmetic";

   function Mat_Scalar_Arithmetic_Into
     (Source      : Mat_Handle;
      Value       : access constant Scalar;
      Operation   : C_Int32;
      Destination : Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_scalar_arithmetic_into";

   function Mat_Compare_Scalar
     (Source : Mat_Handle;
      Value  : C_Double;
      Kind   : C_Int32;
      Result : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_compare_scalar";

   function Mat_Compare_Scalar_Into
     (Source      : Mat_Handle;
      Value       : C_Double;
      Kind        : C_Int32;
      Destination : Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_compare_scalar_into";

   Compare_Equal            : constant C_Int32 := 0;
   Compare_Not_Equal        : constant C_Int32 := 1;
   Compare_Less_Than        : constant C_Int32 := 2;
   Compare_Less_Or_Equal    : constant C_Int32 := 3;
   Compare_Greater_Than     : constant C_Int32 := 4;
   Compare_Greater_Or_Equal : constant C_Int32 := 5;

   Flip_Vertical   : constant C_Int32 := 0;
   Flip_Horizontal : constant C_Int32 := 1;
   Flip_Both_Axes  : constant C_Int32 := C_Int32'Val (-1);

   Border_Constant    : constant C_Int32 := 0;
   Border_Replicate   : constant C_Int32 := 1;
   Border_Reflect     : constant C_Int32 := 2;
   Border_Reflect_101 : constant C_Int32 := 3;
   Border_Wrap        : constant C_Int32 := 4;

   Rotate_90_Clockwise        : constant C_Int32 := 0;
   Rotate_180                 : constant C_Int32 := 1;
   Rotate_90_Counterclockwise : constant C_Int32 := 2;

   Reduce_Across_Rows    : constant C_Int32 := 0;
   Reduce_Across_Columns : constant C_Int32 := 1;

   Reduce_Sum            : constant C_Int32 := 0;
   Reduce_Average        : constant C_Int32 := 1;
   Reduce_Maximum        : constant C_Int32 := 2;
   Reduce_Minimum        : constant C_Int32 := 3;
   Reduce_Sum_Of_Squares : constant C_Int32 := 4;

   Default_Output_Depth : constant C_Int32 := C_Int32'Val (-1);

   Transposed_Product_Transpose_Times_Self : constant C_UInt8 := 0;
   Transposed_Product_Self_Times_Transpose : constant C_UInt8 := 1;

   Sample_Orientation_Rows    : constant C_Int32 := 0;
   Sample_Orientation_Columns : constant C_Int32 := 1;

   Covariance_Scaling_Unscaled        : constant C_Int32 := 0;
   Covariance_Scaling_By_Sample_Count : constant C_Int32 := 1;
   DFT_Forward_Complex                : constant C_Int32 := 0;
   DFT_Inverse_Complex                : constant C_Int32 := 1;
   DFT_Inverse_Real                   : constant C_Int32 := 2;
   DFT_Rows_Forward_Complex           : constant C_Int32 := 3;
   DFT_Rows_Inverse_Complex           : constant C_Int32 := 4;
   DFT_Rows_Inverse_Real              : constant C_Int32 := 5;
   DFT_Forward_Packed                 : constant C_Int32 := 6;
   DFT_Inverse_Packed                 : constant C_Int32 := 7;
   DFT_Rows_Forward_Packed            : constant C_Int32 := 8;
   DFT_Rows_Inverse_Packed            : constant C_Int32 := 9;
   DCT_Forward                        : constant C_Int32 := 0;
   DCT_Inverse                        : constant C_Int32 := 1;
   DCT_Rows_Forward                   : constant C_Int32 := 2;
   DCT_Rows_Inverse                   : constant C_Int32 := 3;

   Spectrum_Product_Ordinary               : constant C_Int32 := 0;
   Spectrum_Product_Conjugate_Right        : constant C_Int32 := 1;
   Spectrum_Representation_Full_Complex    : constant C_Int32 := 0;
   Spectrum_Representation_Packed_CCS      : constant C_Int32 := 1;
   Spectrum_Representation_Packed_CCS_Rows : constant C_Int32 := 2;

   K_Means_Random_Centers    : constant C_Int32 := 0;
   K_Means_Plus_Plus_Centers : constant C_Int32 := 1;

   Batch_Distance_L1         : constant C_Int32 := 0;
   Batch_Distance_L2         : constant C_Int32 := 1;
   Batch_Distance_Squared_L2 : constant C_Int32 := 2;
   Batch_Distance_Hamming    : constant C_Int32 := 3;
   Batch_Distance_Hamming_2  : constant C_Int32 := 4;

   subtype C_Boolean is Interfaces.Unsigned_8;
   C_False : constant C_Boolean := 0;
   C_True  : constant C_Boolean := 1;

   function Last_Error_Message return String;

   function Set_RNG_Seed (Seed : C_Int32) return Status
   with Import, Convention => C, External_Name => "opencv_core_set_rng_seed";

   function Mat_Create (Result : access Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_create";

   function Mat_Create_2D
     (Rows     : C_Int32;
      Columns  : C_Int32;
      Depth    : C_Int32;
      Channels : C_Int32;
      Result   : access Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_create_2d";

   function Mat_Create_ND
     (Dimension_Count : C_Int32;
      Sizes           : access C_Int32;
      Depth           : C_Int32;
      Channels        : C_Int32;
      Result          : access Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_create_nd";

   function Mat_Create_External_2D
     (Rows       : C_Int32;
      Columns    : C_Int32;
      Depth      : C_Int32;
      Channels   : C_Int32;
      Data       : System.Address;
      Byte_Count : C_UInt64;
      Result     : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_create_external_2d";

   function Mat_Create_External_2D_Strided
     (Rows             : C_Int32;
      Columns          : C_Int32;
      Depth            : C_Int32;
      Channels         : C_Int32;
      Data             : System.Address;
      Byte_Count       : C_UInt64;
      Row_Stride_Bytes : C_UInt64;
      Result           : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_create_external_2d_strided";

   function Mat_Create_External_ND
     (Dimension_Count : C_Int32;
      Sizes           : access C_Int32;
      Depth           : C_Int32;
      Channels        : C_Int32;
      Data            : System.Address;
      Byte_Count      : C_UInt64;
      Result          : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_create_external_nd";

   --  Element_Strides holds Dimension_Count complete-element strides; the
   --  shim constructs its own full native size_t step array.
   function Mat_Create_External_ND_Strided
     (Dimension_Count : C_Int32;
      Sizes           : access C_Int32;
      Element_Strides : access C_UInt64;
      Depth           : C_Int32;
      Channels        : C_Int32;
      Data            : System.Address;
      Byte_Count      : C_UInt64;
      Result          : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_create_external_nd_strided";

   function Mat_Copy
     (Source : Mat_Handle; Result : access Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_copy";

   function Mat_Acquire_Borrow_Lease
     (Source : Mat_Handle; Result : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_acquire_borrow_lease";

   function Mat_Resolve_Output
     (Destination : Mat_Handle; Result : access System.Address) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_resolve_output";

   function UMat_Resolve_Input
     (Source : UMat_Handle; Result : access System.Address) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_resolve_input";

   function UMat_Resolve_Output
     (Destination : UMat_Handle; Result : access System.Address) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_resolve_output";

   function Sparse_Resolve_Input
     (Source : Sparse_Mat_Handle; Result : access System.Address) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_resolve_input";

   function Sparse_Resolve_Output
     (Destination : Sparse_Mat_Handle; Result : access System.Address)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_resolve_output";

   function Mat_Clone
     (Source : Mat_Handle; Result : access Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_clone";

   function Mat_K_Means
     (Samples            : Mat_Handle;
      Cluster_Count      : C_Int32;
      Maximum_Iterations : C_Int32;
      Epsilon            : C_Double;
      Attempts           : C_Int32;
      Initialization     : C_Int32;
      Labels             : access Mat_Handle;
      Centers            : access Mat_Handle;
      Compactness        : access C_Double) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_kmeans";

   function Mat_K_Means_With_Initial_Labels
     (Samples                   : Mat_Handle;
      Initial_Labels            : Mat_Handle;
      Cluster_Count             : C_Int32;
      Maximum_Iterations        : C_Int32;
      Epsilon                   : C_Double;
      Attempts                  : C_Int32;
      Subsequent_Initialization : C_Int32;
      Labels                    : access Mat_Handle;
      Centers                   : access Mat_Handle;
      Compactness               : access C_Double) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_kmeans_with_initial_labels";

   function Mat_Batch_Distance
     (Queries        : Mat_Handle;
      Candidates     : Mat_Handle;
      Neighbor_Count : C_Int32;
      Kind           : C_Int32;
      Distances      : access Mat_Handle;
      Indices        : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_batch_distance";

   function Mat_Transpose
     (Source : Mat_Handle; Result : access Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_transpose";

   function Mat_Flip
     (Source : Mat_Handle; Kind : C_Int32; Result : access Mat_Handle)
      return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_flip";

   function Mat_Sort
     (Source     : Mat_Handle;
      Axis       : C_UInt8;
      Descending : C_UInt8;
      Result     : access Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_sort";

   function Mat_Sort_Indices
     (Source     : Mat_Handle;
      Axis       : C_UInt8;
      Descending : C_UInt8;
      Result     : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_sort_indices";

   function Mat_Copy_Make_Border
     (Source   : Mat_Handle;
      Top      : C_Int32;
      Bottom   : C_Int32;
      Left     : C_Int32;
      Right    : C_Int32;
      Kind     : C_Int32;
      Value    : access Scalar;
      Isolated : C_Boolean;
      Result   : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_copy_make_border";

   function Border_Interpolate
     (Position : C_Int32;
      Length   : C_Int32;
      Kind     : C_Int32;
      Index    : access C_Int32) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_border_interpolate";

   function Mat_Rotate
     (Source : Mat_Handle; Kind : C_Int32; Result : access Mat_Handle)
      return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_rotate";

   function Mat_Repeat
     (Source             : Mat_Handle;
      Row_Repetitions    : C_Int32;
      Column_Repetitions : C_Int32;
      Result             : access Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_repeat";

   function Mat_Reduce
     (Source       : Mat_Handle;
      Axis         : C_Int32;
      Kind         : C_Int32;
      Output_Depth : C_Int32;
      Result       : access Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_reduce";

   function Mat_Reduce_Arg_Min
     (Source     : Mat_Handle;
      Axis       : C_Int32;
      Last_Index : C_UInt8;
      Result     : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_reduce_arg_min";

   function Mat_Reduce_Arg_Max
     (Source     : Mat_Handle;
      Axis       : C_Int32;
      Last_Index : C_UInt8;
      Result     : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_reduce_arg_max";

   function Mat_HConcat
     (Sources : access Mat_Handle; Count : C_Int32; Result : access Mat_Handle)
      return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_hconcat";

   function Mat_VConcat
     (Sources : access Mat_Handle; Count : C_Int32; Result : access Mat_Handle)
      return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_vconcat";

   function Mat_Split
     (Source : Mat_Handle; Results : access Mat_Handle; Count : C_Int32)
      return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_split";

   function Mat_Extract_Channel
     (Source : Mat_Handle; Channel : C_Int32; Result : access Mat_Handle)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_extract_channel";

   function Mat_Insert_Channel
     (Source, Destination : Mat_Handle; Channel : C_Int32) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_insert_channel";

   function Mat_Mix_Channels
     (Sources           : access Mat_Handle;
      Source_Count      : C_Int32;
      Destinations      : access Mat_Handle;
      Destination_Count : C_Int32;
      From_To           : access C_Int32;
      Pair_Count        : C_Int32) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_mix_channels";

   function Mat_Merge
     (Sources : access Mat_Handle; Count : C_Int32; Result : access Mat_Handle)
      return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_merge";

   function Mat_Copy_To (Source, Destination : Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_copy_to";

   function Mat_Copy_To_Masked
     (Source, Destination, Mask : Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_copy_to_masked";

   function Mat_Convert_To
     (Source : Mat_Handle;
      Depth  : C_Int32;
      Scale  : C_Double;
      Offset : C_Double;
      Result : access Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_convert_to";

   function Mat_Convert_To_Into
     (Source, Destination : Mat_Handle;
      Depth               : C_Int32;
      Scale, Offset       : C_Double) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_convert_to_into";

   function Mat_Convert_Scale_Abs
     (Source : Mat_Handle;
      Scale  : C_Double;
      Offset : C_Double;
      Result : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_convert_scale_abs";

   function Mat_Apply_LUT
     (Source, Table : Mat_Handle; Result : access Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_apply_lut";

   function Mat_Sqrt_Into (Source, Destination : Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_sqrt_into";
   function Mat_Exp_Into (Source, Destination : Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_exp_into";
   function Mat_Log_Into (Source, Destination : Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_log_into";
   function Mat_Pow_Into
     (Source : Mat_Handle; Power : C_Double; Destination : Mat_Handle)
      return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_pow_into";

   function Mat_Sqrt
     (Source : Mat_Handle; Result : access Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_sqrt";

   function Mat_Exp
     (Source : Mat_Handle; Result : access Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_exp";

   function Mat_Log
     (Source : Mat_Handle; Result : access Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_log";

   function Mat_Pow
     (Source : Mat_Handle; Power : C_Double; Result : access Mat_Handle)
      return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_pow";

   function Mat_Magnitude
     (X, Y : Mat_Handle; Result : access Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_magnitude";

   function Mat_Magnitude_Into (X, Y, Destination : Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_magnitude_into";

   function Mat_Phase_Into
     (X, Y             : Mat_Handle;
      Angle_In_Degrees : C_Boolean;
      Destination      : Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_phase_into";

   function Mat_Phase
     (X, Y             : Mat_Handle;
      Angle_In_Degrees : C_Boolean;
      Result           : access Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_phase";
   function Mat_Cart_To_Polar
     (X, Y             : Mat_Handle;
      Angle_In_Degrees : C_Boolean;
      Magnitude        : access Mat_Handle;
      Angle            : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_cart_to_polar";

   function Mat_Polar_To_Cart
     (Magnitude, Angle : Mat_Handle;
      Angle_In_Degrees : C_Boolean;
      X                : access Mat_Handle;
      Y                : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_polar_to_cart";

   function Mat_Cart_To_Polar_Into
     (X, Y             : Mat_Handle;
      Angle_In_Degrees : C_Boolean;
      Magnitude, Angle : Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_cart_to_polar_into";
   function Mat_Polar_To_Cart_Into
     (Magnitude, Angle : Mat_Handle;
      Angle_In_Degrees : C_Boolean;
      X, Y             : Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_polar_to_cart_into";

   function Mat_Normalize
     (Source : Mat_Handle;
      Kind   : C_Int32;
      Alpha  : C_Double;
      Beta   : C_Double;
      Result : access Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_normalize";

   function Mat_Normalize_Into
     (Source, Destination : Mat_Handle; Kind : C_Int32; Alpha, Beta : C_Double)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_normalize_into";

   function Mat_Add
     (Left, Right : Mat_Handle; Result : access Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_add";

   function Mat_Add_Into (Left, Right, Destination : Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_add_into";

   function Mat_Subtract_Into
     (Left, Right, Destination : Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_subtract_into";

   function UMat_Add_Into
     (Left, Right, Destination : UMat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_umat_add_into";

   function UMat_Subtract_Into
     (Left, Right, Destination : UMat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_subtract_into";

   function Mat_Subtract
     (Left, Right : Mat_Handle; Result : access Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_subtract";

   function Mat_Multiply
     (Left, Right : Mat_Handle; Result : access Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_multiply";

   function Mat_Multiply_Into
     (Left, Right, Destination : Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_multiply_into";

   function UMat_Multiply_Into
     (Left, Right, Destination : UMat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_multiply_into";

   function Mat_Divide
     (Left, Right : Mat_Handle; Result : access Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_divide";

   function Mat_Divide_Into
     (Left, Right, Destination : Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_divide_into";

   function UMat_Divide_Into
     (Left, Right, Destination : UMat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_divide_into";

   function Mat_Abs_Diff_Into
     (Left, Right, Destination : Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_abs_diff_into";

   function UMat_Abs_Diff_Into
     (Left, Right, Destination : UMat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_abs_diff_into";

   function Mat_Abs_Diff
     (Left, Right : Mat_Handle; Result : access Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_abs_diff";

   function Mat_Minimum
     (Left, Right : Mat_Handle; Result : access Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_minimum";

   function Mat_Minimum_Into
     (Left, Right, Destination : Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_minimum_into";

   function Mat_Maximum_Into
     (Left, Right, Destination : Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_maximum_into";

   function UMat_Minimum_Into
     (Left, Right, Destination : UMat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_minimum_into";

   function UMat_Maximum_Into
     (Left, Right, Destination : UMat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_maximum_into";

   function Mat_Maximum
     (Left, Right : Mat_Handle; Result : access Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_maximum";

   function UMat_Add
     (Left, Right : UMat_Handle; Result : access UMat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_umat_add";
   function UMat_Subtract
     (Left, Right : UMat_Handle; Result : access UMat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_umat_subtract";
   function UMat_Multiply
     (Left, Right : UMat_Handle; Result : access UMat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_umat_multiply";
   function UMat_Divide
     (Left, Right : UMat_Handle; Result : access UMat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_umat_divide";
   function UMat_Abs_Diff
     (Left, Right : UMat_Handle; Result : access UMat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_umat_abs_diff";
   function UMat_Minimum
     (Left, Right : UMat_Handle; Result : access UMat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_umat_minimum";
   function UMat_Maximum
     (Left, Right : UMat_Handle; Result : access UMat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_umat_maximum";

   function Mat_Add_Weighted
     (Left   : Mat_Handle;
      Alpha  : C_Double;
      Right  : Mat_Handle;
      Beta   : C_Double;
      Gamma  : C_Double;
      Result : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_add_weighted";

   function Mat_Scale_Add
     (Left   : Mat_Handle;
      Scale  : C_Double;
      Right  : Mat_Handle;
      Result : access Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_scale_add";

   function UMat_Add_Weighted
     (Left   : UMat_Handle;
      Alpha  : C_Double;
      Right  : UMat_Handle;
      Beta   : C_Double;
      Gamma  : C_Double;
      Result : access UMat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_add_weighted";

   function UMat_Scale_Add
     (Left   : UMat_Handle;
      Scale  : C_Double;
      Right  : UMat_Handle;
      Result : access UMat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_umat_scale_add";

   function Mat_Add_Weighted_Into
     (Left        : Mat_Handle;
      Alpha       : C_Double;
      Right       : Mat_Handle;
      Beta, Gamma : C_Double;
      Destination : Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_add_weighted_into";
   function Mat_Scale_Add_Into
     (Left        : Mat_Handle;
      Scale       : C_Double;
      Right       : Mat_Handle;
      Destination : Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_scale_add_into";
   function UMat_Add_Weighted_Into
     (Left        : UMat_Handle;
      Alpha       : C_Double;
      Right       : UMat_Handle;
      Beta, Gamma : C_Double;
      Destination : UMat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_add_weighted_into";
   function UMat_Scale_Add_Into
     (Left        : UMat_Handle;
      Scale       : C_Double;
      Right       : UMat_Handle;
      Destination : UMat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_scale_add_into";

   function Mat_Bitwise_And_Into
     (Left, Right, Destination : Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_bitwise_and_into";
   function Mat_Bitwise_And_Masked_Into
     (Left, Right, Mask, Destination : Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_bitwise_and_masked_into";
   function Mat_Bitwise_Or_Into
     (Left, Right, Destination : Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_bitwise_or_into";
   function Mat_Bitwise_Or_Masked_Into
     (Left, Right, Mask, Destination : Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_bitwise_or_masked_into";
   function Mat_Bitwise_Xor_Into
     (Left, Right, Destination : Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_bitwise_xor_into";
   function Mat_Bitwise_Xor_Masked_Into
     (Left, Right, Mask, Destination : Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_bitwise_xor_masked_into";
   function Mat_Bitwise_Not_Into (Self, Destination : Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_bitwise_not_into";
   function Mat_Bitwise_Not_Masked_Into
     (Self, Mask, Destination : Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_bitwise_not_masked_into";
   function UMat_Bitwise_And_Into
     (Left, Right, Destination : UMat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_bitwise_and_into";
   function UMat_Bitwise_And_Masked_Into
     (Left, Right, Mask, Destination : UMat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_bitwise_and_masked_into";
   function UMat_Bitwise_Or_Into
     (Left, Right, Destination : UMat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_bitwise_or_into";
   function UMat_Bitwise_Or_Masked_Into
     (Left, Right, Mask, Destination : UMat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_bitwise_or_masked_into";
   function UMat_Bitwise_Xor_Into
     (Left, Right, Destination : UMat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_bitwise_xor_into";
   function UMat_Bitwise_Xor_Masked_Into
     (Left, Right, Mask, Destination : UMat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_bitwise_xor_masked_into";
   function UMat_Bitwise_Not_Into
     (Self, Destination : UMat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_bitwise_not_into";
   function UMat_Bitwise_Not_Masked_Into
     (Self, Mask, Destination : UMat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_bitwise_not_masked_into";

   function UMat_Bitwise_And
     (Left, Right : UMat_Handle; Result : access UMat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_bitwise_and";
   function UMat_Bitwise_Or
     (Left, Right : UMat_Handle; Result : access UMat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_bitwise_or";
   function UMat_Bitwise_Xor
     (Left, Right : UMat_Handle; Result : access UMat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_bitwise_xor";
   function UMat_Bitwise_Not
     (Self : UMat_Handle; Result : access UMat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_bitwise_not";
   function UMat_Bitwise_And_Masked
     (Left, Right, Mask : UMat_Handle; Result : access UMat_Handle)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_bitwise_and_masked";
   function UMat_Bitwise_Or_Masked
     (Left, Right, Mask : UMat_Handle; Result : access UMat_Handle)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_bitwise_or_masked";
   function UMat_Bitwise_Xor_Masked
     (Left, Right, Mask : UMat_Handle; Result : access UMat_Handle)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_bitwise_xor_masked";
   function UMat_Bitwise_Not_Masked
     (Self, Mask : UMat_Handle; Result : access UMat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_bitwise_not_masked";
   function UMat_In_Range_Scalar
     (Self         : UMat_Handle;
      Lower, Upper : access constant Scalar;
      Result       : access UMat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_in_range_scalar";
   function UMat_Normalize
     (Source      : UMat_Handle;
      Kind        : C_Int32;
      Alpha, Beta : C_Double;
      Result      : access UMat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_umat_normalize";
   function UMat_Normalize_Into
     (Source, Destination : UMat_Handle;
      Kind                : C_Int32;
      Alpha, Beta         : C_Double) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_normalize_into";

   function UMat_Sqrt_Into (Source, Destination : UMat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_umat_sqrt_into";
   function UMat_Exp_Into (Source, Destination : UMat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_umat_exp_into";
   function UMat_Log_Into (Source, Destination : UMat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_umat_log_into";
   function UMat_Pow_Into
     (Source : UMat_Handle; Power : C_Double; Destination : UMat_Handle)
      return Status
   with Import, Convention => C, External_Name => "opencv_core_umat_pow_into";

   function UMat_Sqrt
     (Source : UMat_Handle; Result : access UMat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_umat_sqrt";
   function UMat_Exp
     (Source : UMat_Handle; Result : access UMat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_umat_exp";
   function UMat_Log
     (Source : UMat_Handle; Result : access UMat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_umat_log";
   function UMat_Pow
     (Source : UMat_Handle; Power : C_Double; Result : access UMat_Handle)
      return Status
   with Import, Convention => C, External_Name => "opencv_core_umat_pow";
   function UMat_Magnitude
     (X, Y : UMat_Handle; Result : access UMat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_umat_magnitude";
   function UMat_Magnitude_Into (X, Y, Destination : UMat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_magnitude_into";
   function UMat_Phase_Into
     (X, Y             : UMat_Handle;
      Angle_In_Degrees : C_Boolean;
      Destination      : UMat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_phase_into";
   function UMat_Phase
     (X, Y             : UMat_Handle;
      Angle_In_Degrees : C_Boolean;
      Result           : access UMat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_umat_phase";
   function UMat_Cart_To_Polar
     (X, Y             : UMat_Handle;
      Angle_In_Degrees : C_Boolean;
      Magnitude, Angle : access UMat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_cart_to_polar";
   function UMat_Polar_To_Cart
     (Magnitude, Angle : UMat_Handle;
      Angle_In_Degrees : C_Boolean;
      X, Y             : access UMat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_polar_to_cart";

   function UMat_Cart_To_Polar_Into
     (X, Y             : UMat_Handle;
      Angle_In_Degrees : C_Boolean;
      Magnitude, Angle : UMat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_cart_to_polar_into";
   function UMat_Polar_To_Cart_Into
     (Magnitude, Angle : UMat_Handle;
      Angle_In_Degrees : C_Boolean;
      X, Y             : UMat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_polar_to_cart_into";

   function UMat_Compare
     (Left, Right : UMat_Handle; Kind : C_Int32; Result : access UMat_Handle)
      return Status
   with Import, Convention => C, External_Name => "opencv_core_umat_compare";

   function Mat_Bitwise_And
     (Left, Right : Mat_Handle; Result : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_bitwise_and";

   function Mat_Bitwise_Or
     (Left, Right : Mat_Handle; Result : access Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_bitwise_or";

   function Mat_Bitwise_Xor
     (Left, Right : Mat_Handle; Result : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_bitwise_xor";

   function Mat_Bitwise_Not
     (Self : Mat_Handle; Result : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_bitwise_not";

   function Mat_Bitwise_And_Masked
     (Left, Right, Mask : Mat_Handle; Result : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_bitwise_and_masked";

   function Mat_Bitwise_Or_Masked
     (Left, Right, Mask : Mat_Handle; Result : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_bitwise_or_masked";

   function Mat_Bitwise_Xor_Masked
     (Left, Right, Mask : Mat_Handle; Result : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_bitwise_xor_masked";

   function Mat_Bitwise_Not_Masked
     (Self, Mask : Mat_Handle; Result : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_bitwise_not_masked";

   function Mat_In_Range_Scalar
     (Self   : Mat_Handle;
      Lower  : access constant Scalar;
      Upper  : access constant Scalar;
      Result : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_in_range_scalar";

   function Mat_Compare
     (Left, Right : Mat_Handle; Kind : C_Int32; Result : access Mat_Handle)
      return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_compare";

   function Mat_Compare_Into
     (Left, Right : Mat_Handle; Kind : C_Int32; Destination : Mat_Handle)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_compare_into";
   function UMat_Compare_Into
     (Left, Right : UMat_Handle; Kind : C_Int32; Destination : UMat_Handle)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_compare_into";
   function Mat_In_Range_Scalar_Into
     (Self         : Mat_Handle;
      Lower, Upper : access constant Scalar;
      Destination  : Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_in_range_scalar_into";
   function UMat_In_Range_Scalar_Into
     (Self         : UMat_Handle;
      Lower, Upper : access constant Scalar;
      Destination  : UMat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_umat_in_range_scalar_into";

   function Mat_Region
     (Source : Mat_Handle;
      X      : C_Int32;
      Y      : C_Int32;
      Width  : C_Int32;
      Height : C_Int32;
      Result : access Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_region";

   function Mat_Locate_ROI
     (Source                                        : Mat_Handle;
      Whole_Width, Whole_Height, Offset_X, Offset_Y : access C_Int32)
      return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_locate_roi";
   function Mat_Adjust_ROI
     (Self : Mat_Handle; Top, Bottom, Left, Right : C_Int32) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_adjust_roi";

   function Mat_Row_View
     (Source : Mat_Handle; Row : C_Int32; Result : access Mat_Handle)
      return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_row_view";

   function Mat_Column_View
     (Source : Mat_Handle; Column : C_Int32; Result : access Mat_Handle)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_column_view";

   function Mat_Row_Range_View
     (Source : Mat_Handle;
      Start  : C_Int32;
      Stop   : C_Int32;
      Result : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_row_range_view";

   function Mat_Column_Range_View
     (Source : Mat_Handle;
      Start  : C_Int32;
      Stop   : C_Int32;
      Result : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_column_range_view";

   function Mat_Slice_ND
     (Source          : Mat_Handle;
      Dimension_Count : C_Int32;
      Starts          : access C_Int32;
      Stops           : access C_Int32;
      Result          : access Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_slice_nd";

   --  Drop_Flags, Starts, and Stops each hold Dimension_Count entries.
   --  Drop flag 0 retains [Start, Stop); 1 fixes Start and drops the
   --  dimension (Stop must be Start + 1). The result is a temporary view.
   function Mat_Select_ND_View
     (Source          : Mat_Handle;
      Dimension_Count : C_Int32;
      Drop_Flags      : access C_UInt8;
      Starts          : access C_Int32;
      Stops           : access C_Int32;
      Result          : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_select_nd_view";

   function Mat_Reshape
     (Source   : Mat_Handle;
      Channels : C_Int32;
      Rows     : C_Int32;
      Result   : access Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_reshape";

   function Mat_Reshape_ND
     (Source          : Mat_Handle;
      Channels        : C_Int32;
      Dimension_Count : C_Int32;
      Sizes           : access constant C_Int32;
      Result          : access Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_reshape_nd";

   function Mat_Diagonal_Matrix
     (Diagonal : Mat_Handle; Result : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_diagonal_matrix";

   function Mat_Diagonal_View
     (Source : Mat_Handle; Offset : C_Int32; Result : access Mat_Handle)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_diagonal_view";

   procedure Mat_Destroy (Self : Mat_Handle)
   with Import, Convention => C, External_Name => "opencv_core_mat_destroy";

   function Mat_Is_Empty
     (Self : Mat_Handle; Result : access C_Boolean) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_is_empty";

   function Mat_Rows (Self : Mat_Handle; Result : access C_Int32) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_rows";

   function Mat_Columns
     (Self : Mat_Handle; Result : access C_Int32) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_columns";

   function Mat_Dimension_Count
     (Self : Mat_Handle; Result : access C_Int32) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_dimension_count";

   function Mat_Extent
     (Self : Mat_Handle; Axis : C_Int32; Result : access C_Int32) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_extent";

   function Mat_Channels
     (Self : Mat_Handle; Result : access C_Int32) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_channels";

   function Mat_Depth
     (Self : Mat_Handle; Result : access C_Int32) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_depth";

   function Mat_Total
     (Self : Mat_Handle; Result : access C_UInt64) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_total";

   function Mat_Element_Size
     (Self : Mat_Handle; Result : access C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_element_size";

   function Mat_Channel_Size
     (Self : Mat_Handle; Result : access C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_channel_size";

   function Mat_Is_Continuous
     (Self : Mat_Handle; Result : access C_Boolean) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_is_continuous";

   function Mat_Is_Submatrix
     (Self : Mat_Handle; Result : access C_Boolean) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_is_submatrix";

   function Mat_Get_UInt8
     (Self : Mat_Handle; Row, Column : C_Int32; Result : access C_UInt8)
      return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_get_uint8";

   function Mat_Set_UInt8
     (Self : Mat_Handle; Row, Column : C_Int32; Value : C_UInt8) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_set_uint8";

   function Mat_Get_Int8
     (Self : Mat_Handle; Row, Column : C_Int32; Result : access C_Int8)
      return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_get_int8";

   function Mat_Set_Int8
     (Self : Mat_Handle; Row, Column : C_Int32; Value : C_Int8) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_set_int8";

   function Mat_Get_UInt16
     (Self : Mat_Handle; Row, Column : C_Int32; Result : access C_UInt16)
      return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_get_uint16";

   function Mat_Set_UInt16
     (Self : Mat_Handle; Row, Column : C_Int32; Value : C_UInt16) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_set_uint16";

   function Mat_Get_Int16
     (Self : Mat_Handle; Row, Column : C_Int32; Result : access C_Int16)
      return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_get_int16";

   function Mat_Set_Int16
     (Self : Mat_Handle; Row, Column : C_Int32; Value : C_Int16) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_set_int16";

   function Mat_Get_Int32
     (Self : Mat_Handle; Row, Column : C_Int32; Result : access C_Int32)
      return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_get_int32";

   function Mat_Set_Int32
     (Self : Mat_Handle; Row, Column : C_Int32; Value : C_Int32) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_set_int32";

   function Mat_Get_Float32
     (Self : Mat_Handle; Row, Column : C_Int32; Result : access C_Float32)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_float32";

   Float32_Finite            : constant C_Int32 := 0;
   Float32_Positive_Infinity : constant C_Int32 := 1;
   Float32_Negative_Infinity : constant C_Int32 := 2;
   Float32_Not_A_Number      : constant C_Int32 := 3;

   function Mat_Classify_Float32
     (Self : Mat_Handle; Row, Column : C_Int32; Result : access C_Int32)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_classify_float32";

   function Mat_Set_Float32
     (Self : Mat_Handle; Row, Column : C_Int32; Value : C_Float32)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_float32";

   Float64_Finite            : constant C_Int32 := 0;
   Float64_Positive_Infinity : constant C_Int32 := 1;
   Float64_Negative_Infinity : constant C_Int32 := 2;
   Float64_Not_A_Number      : constant C_Int32 := 3;

   function Mat_Get_Float64
     (Self : Mat_Handle; Row, Column : C_Int32; Result : access C_Float64)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_float64";

   function Mat_Classify_Float64
     (Self : Mat_Handle; Row, Column : C_Int32; Result : access C_Int32)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_classify_float64";

   function Mat_Set_Float64
     (Self : Mat_Handle; Row, Column : C_Int32; Value : C_Float64)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_float64";

   --  uint16_t carries the stored IEEE binary16 encoding, not an
   --  integer pixel.
   function Mat_Get_Float16
     (Self : Mat_Handle; Row, Column : C_Int32; Result : access C_UInt16)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_float16";

   function Mat_Set_Float16
     (Self : Mat_Handle; Row, Column : C_Int32; Value : C_UInt16) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_float16";

   function Mat_Get_UInt8_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Result          : access C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_uint8_nd";

   function Mat_Get_Float64_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Result          : access C_Float64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_float64_nd";

   function Mat_Set_Float64_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Value           : C_Float64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_float64_nd";

   --  uint16_t carries the stored IEEE binary16 encoding, not an
   --  integer pixel.
   function Mat_Get_Float16_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Result          : access C_UInt16) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_float16_nd";

   function Mat_Set_Float16_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Value           : C_UInt16) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_float16_nd";

   function Mat_Set_UInt8_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Value           : C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_uint8_nd";

   function Mat_Get_Int8_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Result          : access C_Int8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_int8_nd";

   function Mat_Set_Int8_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Value           : C_Int8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_int8_nd";

   function Mat_Get_UInt16_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Result          : access C_UInt16) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_uint16_nd";

   function Mat_Set_UInt16_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Value           : C_UInt16) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_uint16_nd";

   function Mat_Get_Int16_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Result          : access C_Int16) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_int16_nd";

   function Mat_Set_Int16_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Value           : C_Int16) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_int16_nd";

   function Mat_Get_Int32_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Result          : access C_Int32) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_int32_nd";

   function Mat_Set_Int32_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Value           : C_Int32) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_int32_nd";

   function Mat_Get_Float32_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Result          : access C_Float32) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_float32_nd";

   function Mat_Set_Float32_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Value           : C_Float32) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_float32_nd";

   function Mat_Read_UInt8_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_read_uint8_row";

   function Mat_Write_UInt8_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_write_uint8_row";

   function Mat_Read_Int8_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_read_int8_row";

   function Mat_Write_Int8_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_write_int8_row";

   function Mat_Read_UInt16_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_read_uint16_row";

   function Mat_Write_UInt16_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_write_uint16_row";

   function Mat_Read_Int16_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_read_int16_row";

   function Mat_Write_Int16_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_write_int16_row";

   function Mat_Read_Int32_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_read_int32_row";

   function Mat_Write_Int32_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_write_int32_row";

   function Mat_Read_Float32_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_read_float32_row";

   function Mat_Write_Float32_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_write_float32_row";

   function Mat_Read_Float64_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_read_float64_row";

   function Mat_Write_Float64_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_write_float64_row";

   --  uint16_t carries the stored IEEE binary16 encoding, not an
   --  integer pixel.
   function Mat_Read_Float16_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_read_float16_row";

   function Mat_Write_Float16_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_write_float16_row";

   function Mat_Borrow_Row_Data
     (Self           : Mat_Handle;
      Row            : C_Int32;
      Data           : access System.Address;
      Out_Byte_Count : access C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_borrow_row_data";

   --  Complete logical storage of a continuous Mat of any dimensionality.
   --  A zero-element Mat succeeds with a null address and zero bytes.
   function Mat_Borrow_Contiguous_Data
     (Self           : Mat_Handle;
      Data           : access System.Address;
      Out_Byte_Count : access C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_borrow_contiguous_data";

   function Mat_Get_UInt8_Vec3
     (Self   : Mat_Handle;
      Row    : C_Int32;
      Column : C_Int32;
      Result : access UInt8_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_uint8_vec3";

   function Mat_Set_UInt8_Vec3
     (Self   : Mat_Handle;
      Row    : C_Int32;
      Column : C_Int32;
      Value  : access constant UInt8_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_uint8_vec3";

   function Mat_Get_UInt8_Vec2
     (Self : Mat_Handle; Row, Column : C_Int32; Result : access UInt8_Vec2)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_uint8_vec2";
   function Mat_Set_UInt8_Vec2
     (Self        : Mat_Handle;
      Row, Column : C_Int32;
      Value       : access constant UInt8_Vec2) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_uint8_vec2";
   function Mat_Get_UInt8_Vec2_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Result          : access UInt8_Vec2) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_uint8_vec2_nd";
   function Mat_Set_UInt8_Vec2_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Value           : access constant UInt8_Vec2) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_uint8_vec2_nd";
   function Mat_Read_UInt8_Vec2_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_read_uint8_vec2_row";
   function Mat_Write_UInt8_Vec2_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_write_uint8_vec2_row";

   function Mat_Get_UInt16_Vec2
     (Self : Mat_Handle; Row, Column : C_Int32; Result : access UInt16_Vec2)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_uint16_vec2";
   function Mat_Set_UInt16_Vec2
     (Self        : Mat_Handle;
      Row, Column : C_Int32;
      Value       : access constant UInt16_Vec2) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_uint16_vec2";
   function Mat_Get_UInt16_Vec2_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Result          : access UInt16_Vec2) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_uint16_vec2_nd";
   function Mat_Set_UInt16_Vec2_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Value           : access constant UInt16_Vec2) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_uint16_vec2_nd";
   function Mat_Read_UInt16_Vec2_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_read_uint16_vec2_row";
   function Mat_Write_UInt16_Vec2_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_write_uint16_vec2_row";

   function Mat_Get_Float32_Vec2
     (Self : Mat_Handle; Row, Column : C_Int32; Result : access Float32_Vec2)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_float32_vec2";
   function Mat_Set_Float32_Vec2
     (Self        : Mat_Handle;
      Row, Column : C_Int32;
      Value       : access constant Float32_Vec2) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_float32_vec2";
   function Mat_Get_Float32_Vec2_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Result          : access Float32_Vec2) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_float32_vec2_nd";
   function Mat_Set_Float32_Vec2_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Value           : access constant Float32_Vec2) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_float32_vec2_nd";
   function Mat_Read_Float32_Vec2_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_read_float32_vec2_row";
   function Mat_Write_Float32_Vec2_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_write_float32_vec2_row";

   function Mat_Get_Float64_Vec2
     (Self : Mat_Handle; Row, Column : C_Int32; Result : access Float64_Vec2)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_float64_vec2";
   function Mat_Set_Float64_Vec2
     (Self        : Mat_Handle;
      Row, Column : C_Int32;
      Value       : access constant Float64_Vec2) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_float64_vec2";
   function Mat_Get_Float64_Vec2_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Result          : access Float64_Vec2) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_float64_vec2_nd";
   function Mat_Set_Float64_Vec2_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Value           : access constant Float64_Vec2) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_float64_vec2_nd";
   function Mat_Read_Float64_Vec2_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_read_float64_vec2_row";
   function Mat_Write_Float64_Vec2_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_write_float64_vec2_row";

   function Mat_Get_Float32_Vec3
     (Self   : Mat_Handle;
      Row    : C_Int32;
      Column : C_Int32;
      Result : access Float32_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_float32_vec3";

   function Mat_Get_Float64_Vec3
     (Self : Mat_Handle; Row, Column : C_Int32; Result : access Float64_Vec3)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_float64_vec3";
   function Mat_Set_Float64_Vec3
     (Self        : Mat_Handle;
      Row, Column : C_Int32;
      Value       : access constant Float64_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_float64_vec3";
   function Mat_Get_Float64_Vec3_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Result          : access Float64_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_float64_vec3_nd";
   function Mat_Set_Float64_Vec3_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Value           : access constant Float64_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_float64_vec3_nd";
   function Mat_Read_Float64_Vec3_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_read_float64_vec3_row";
   function Mat_Write_Float64_Vec3_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_write_float64_vec3_row";

   function Mat_Get_UInt8_Vec4
     (Self : Mat_Handle; Row, Column : C_Int32; Result : access UInt8_Vec4)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_uint8_vec4";
   function Mat_Set_UInt8_Vec4
     (Self        : Mat_Handle;
      Row, Column : C_Int32;
      Value       : access constant UInt8_Vec4) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_uint8_vec4";
   function Mat_Get_UInt8_Vec4_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Result          : access UInt8_Vec4) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_uint8_vec4_nd";
   function Mat_Set_UInt8_Vec4_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Value           : access constant UInt8_Vec4) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_uint8_vec4_nd";
   function Mat_Read_UInt8_Vec4_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_read_uint8_vec4_row";
   function Mat_Write_UInt8_Vec4_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_write_uint8_vec4_row";

   function Mat_Get_UInt16_Vec4
     (Self : Mat_Handle; Row, Column : C_Int32; Result : access UInt16_Vec4)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_uint16_vec4";
   function Mat_Set_UInt16_Vec4
     (Self        : Mat_Handle;
      Row, Column : C_Int32;
      Value       : access constant UInt16_Vec4) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_uint16_vec4";
   function Mat_Get_UInt16_Vec4_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Result          : access UInt16_Vec4) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_uint16_vec4_nd";
   function Mat_Set_UInt16_Vec4_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Value           : access constant UInt16_Vec4) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_uint16_vec4_nd";
   function Mat_Read_UInt16_Vec4_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_read_uint16_vec4_row";
   function Mat_Write_UInt16_Vec4_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_write_uint16_vec4_row";

   function Mat_Get_Float32_Vec4
     (Self : Mat_Handle; Row, Column : C_Int32; Result : access Float32_Vec4)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_float32_vec4";
   function Mat_Set_Float32_Vec4
     (Self        : Mat_Handle;
      Row, Column : C_Int32;
      Value       : access constant Float32_Vec4) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_float32_vec4";
   function Mat_Get_Float32_Vec4_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Result          : access Float32_Vec4) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_float32_vec4_nd";
   function Mat_Set_Float32_Vec4_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Value           : access constant Float32_Vec4) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_float32_vec4_nd";
   function Mat_Read_Float32_Vec4_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_read_float32_vec4_row";
   function Mat_Write_Float32_Vec4_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_write_float32_vec4_row";
   function Mat_Get_Float64_Vec4
     (Self : Mat_Handle; Row, Column : C_Int32; Result : access Float64_Vec4)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_float64_vec4";
   function Mat_Set_Float64_Vec4
     (Self        : Mat_Handle;
      Row, Column : C_Int32;
      Value       : access constant Float64_Vec4) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_float64_vec4";
   function Mat_Get_Float64_Vec4_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Result          : access Float64_Vec4) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_float64_vec4_nd";
   function Mat_Set_Float64_Vec4_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Value           : access constant Float64_Vec4) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_float64_vec4_nd";
   function Mat_Read_Float64_Vec4_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_read_float64_vec4_row";
   function Mat_Write_Float64_Vec4_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_write_float64_vec4_row";

   --  Each uint16_t component is the stored IEEE binary16 encoding.
   function Mat_Get_Float16_Vec3
     (Self   : Mat_Handle;
      Row    : C_Int32;
      Column : C_Int32;
      Result : access Float16_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_float16_vec3";

   function Mat_Set_Float16_Vec3
     (Self   : Mat_Handle;
      Row    : C_Int32;
      Column : C_Int32;
      Value  : access constant Float16_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_float16_vec3";

   --  Native UInt16 C3 access, one complete vector per Mat element.
   function Mat_Get_UInt16_Vec3
     (Self : Mat_Handle; Row, Column : C_Int32; Result : access UInt16_Vec3)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_uint16_vec3";
   function Mat_Set_UInt16_Vec3
     (Self        : Mat_Handle;
      Row, Column : C_Int32;
      Value       : access constant UInt16_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_uint16_vec3";
   function Mat_Get_UInt16_Vec3_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Result          : access UInt16_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_uint16_vec3_nd";
   function Mat_Set_UInt16_Vec3_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Value           : access constant UInt16_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_uint16_vec3_nd";
   function Mat_Read_UInt16_Vec3_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_read_uint16_vec3_row";
   function Mat_Write_UInt16_Vec3_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_write_uint16_vec3_row";

   function Mat_Get_UInt8_Vec3_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Result          : access UInt8_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_uint8_vec3_nd";

   function Mat_Set_UInt8_Vec3_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Value           : access constant UInt8_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_uint8_vec3_nd";

   function Mat_Get_Float32_Vec3_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Result          : access Float32_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_float32_vec3_nd";

   function Mat_Set_Float32_Vec3_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Value           : access constant Float32_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_float32_vec3_nd";

   function Mat_Get_Float16_Vec3_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Result          : access Float16_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_get_float16_vec3_nd";

   function Mat_Set_Float16_Vec3_ND
     (Self            : Mat_Handle;
      Dimension_Count : C_Int32;
      Indices         : access C_Int32;
      Value           : access constant Float16_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_float16_vec3_nd";

   function Mat_Set_Float32_Vec3
     (Self   : Mat_Handle;
      Row    : C_Int32;
      Column : C_Int32;
      Value  : access constant Float32_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_float32_vec3";

   function Mat_Read_UInt8_Vec3_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_read_uint8_vec3_row";

   function Mat_Write_UInt8_Vec3_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_write_uint8_vec3_row";

   function Mat_Read_Float32_Vec3_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_read_float32_vec3_row";

   function Mat_Write_Float32_Vec3_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_write_float32_vec3_row";

   --  uint16_t carries stored IEEE binary16 encodings, three per pixel.
   function Mat_Read_Float16_Vec3_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_read_float16_vec3_row";

   function Mat_Write_Float16_Vec3_Row
     (Self          : Mat_Handle;
      Row           : C_Int32;
      Data          : System.Address;
      Element_Count : C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_write_float16_vec3_row";

   function Mat_Set_To (Self : Mat_Handle; Value : access Scalar) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_set_to";

   function UMat_Set_To
     (Self : UMat_Handle; Value : access Scalar) return Status
   with Import, Convention => C, External_Name => "opencv_core_umat_set_to";

   function RNG_Next
     (RNG_State : access C_UInt64; Value : access C_UInt32) return Status
   with Import, Convention => C, External_Name => "opencv_core_rng_next";

   function RNG_Uniform_Double
     (RNG_State                : access C_UInt64;
      Lower_Bound, Upper_Bound : C_Double;
      Value                    : access C_Double) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_rng_uniform_double";

   function Mat_Fill_Uniform
     (Destination : Mat_Handle; Lower_Bound, Upper_Bound : access Scalar)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_fill_uniform";

   function Mat_Fill_Uniform_RNG
     (Destination              : Mat_Handle;
      Lower_Bound, Upper_Bound : access Scalar;
      RNG_State                : access C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_fill_uniform_rng";

   function Mat_Fill_Normal
     (Destination : Mat_Handle; Mean, Standard_Deviation : access Scalar)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_fill_normal";

   function Mat_Fill_Normal_RNG
     (Destination              : Mat_Handle;
      Mean, Standard_Deviation : access Scalar;
      RNG_State                : access C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_fill_normal_rng";

   function Mat_Shuffle (Destination : Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_shuffle";

   function Mat_Shuffle_RNG
     (Destination : Mat_Handle; RNG_State : access C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_shuffle_rng";

   function Mat_Set_To_Masked
     (Self : Mat_Handle; Value : access Scalar; Mask : Mat_Handle)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_to_masked";

   function Mat_Sum (Self : Mat_Handle; Result : access Scalar) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_sum";

   function Mat_Trace (Self : Mat_Handle; Result : access Scalar) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_trace";

   function Mat_Determinant
     (Source : Mat_Handle; Result : access C_Double) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_determinant";

   function Mat_Dot_Product
     (Left, Right : Mat_Handle; Result : access C_Double) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_dot_product";

   function Mat_Mahalanobis_Distance
     (Left               : Mat_Handle;
      Right              : Mat_Handle;
      Inverse_Covariance : Mat_Handle;
      Result             : access C_Double) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_mahalanobis_distance";

   function Mat_Cross_Product
     (Left, Right : Mat_Handle; Result : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_cross_product";

   function Mat_Invert
     (Source     : Mat_Handle;
      Invertible : access C_Boolean;
      Result     : access Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_invert";

   function Mat_Solve
     (Coefficients    : Mat_Handle;
      Right_Hand_Side : Mat_Handle;
      Solved          : access C_Boolean;
      Result          : access Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_solve";

   function Mat_Solve_Least_Squares
     (Coefficients    : Mat_Handle;
      Right_Hand_Side : Mat_Handle;
      Result          : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_solve_least_squares";

   function Solve_Linear_Program
     (Objective            : Mat_Handle;
      Constraints          : Mat_Handle;
      Constraint_Tolerance : C_Double;
      LP_Status            : access C_Int32;
      Solution             : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_solve_linear_program";

   --  Execution status is the function result; Root_Count is solveCubic's
   --  mathematical -1/0/1/2/3 result.
   function Mat_Solve_Cubic
     (Coefficients : Mat_Handle;
      Root_Count   : access C_Int32;
      Result       : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_solve_cubic";

   function Mat_Solve_Poly_Effective_Degree
     (Coefficients            : Mat_Handle;
      Degree                  : access C_Int32;
      Has_Leading_Coefficient : access C_Boolean) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_solve_poly_effective_degree";

   function Mat_Solve_Poly
     (Coefficients       : Mat_Handle;
      Maximum_Iterations : C_Int32;
      Roots              : access Mat_Handle;
      Maximum_Correction : access C_Double) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_solve_poly";

   function Mat_Matrix_Multiply
     (Left, Right : Mat_Handle; Result : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_matrix_multiply";

   function Mat_Matrix_Multiply_Add
     (Left          : Mat_Handle;
      Right         : Mat_Handle;
      Addend        : Mat_Handle;
      Product_Scale : C_Double;
      Addend_Scale  : C_Double;
      Result        : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_matrix_multiply_add";

   function Mat_Transposed_Product
     (Source       : Mat_Handle;
      Order        : C_UInt8;
      Scale        : C_Double;
      Output_Depth : C_Int32;
      Result       : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_transposed_product";

   function Mat_Transposed_Product_With_Delta
     (Source       : Mat_Handle;
      Offset       : Mat_Handle;
      Order        : C_UInt8;
      Scale        : C_Double;
      Output_Depth : C_Int32;
      Result       : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_transposed_product_with_delta";

   function Mat_Covariance
     (Source      : Mat_Handle;
      Orientation : C_Int32;
      Scaling     : C_Int32;
      Covariance  : access Mat_Handle;
      Mean        : access Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_covariance";

   function Mat_Eigen_Decomposition
     (Source       : Mat_Handle;
      Eigenvalues  : access Mat_Handle;
      Eigenvectors : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_eigen_decomposition";

   function Mat_Non_Symmetric_Eigen_Decomposition
     (Source       : Mat_Handle;
      Eigenvalues  : access Mat_Handle;
      Eigenvectors : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_non_symmetric_eigen_decomposition";

   function Mat_Principal_Component_Analysis
     (Source         : Mat_Handle;
      Orientation    : C_Int32;
      Max_Components : C_Int32;
      Mean           : access Mat_Handle;
      Eigenvalues    : access Mat_Handle;
      Eigenvectors   : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_principal_component_analysis";

   function Mat_Linear_Discriminant_Analysis
     (Samples      : Mat_Handle;
      Labels       : Mat_Handle;
      Components   : C_Int32;
      Eigenvalues  : access Mat_Handle;
      Eigenvectors : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_linear_discriminant_analysis";

   function Mat_LDA_Project
     (Source       : Mat_Handle;
      Eigenvectors : Mat_Handle;
      Result       : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_lda_project";

   function Mat_LDA_Reconstruct
     (Coordinates  : Mat_Handle;
      Eigenvectors : Mat_Handle;
      Result       : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_lda_reconstruct";

   function Mat_Principal_Component_Analysis_Retained_Variance
     (Source            : Mat_Handle;
      Orientation       : C_Int32;
      Retained_Variance : C_Double;
      Mean              : access Mat_Handle;
      Eigenvalues       : access Mat_Handle;
      Eigenvectors      : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name =>
       "opencv_core_mat_principal_component_analysis_retained_variance";

   function Mat_PCA_Project
     (Source       : Mat_Handle;
      Mean         : Mat_Handle;
      Eigenvectors : Mat_Handle;
      Orientation  : C_Int32;
      Result       : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_pca_project";

   function Mat_PCA_Back_Project
     (Source       : Mat_Handle;
      Mean         : Mat_Handle;
      Eigenvectors : Mat_Handle;
      Orientation  : C_Int32;
      Result       : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_pca_back_project";

   function Mat_Singular_Value_Decomposition
     (Source          : Mat_Handle;
      Singular_Values : access Mat_Handle;
      U               : access Mat_Handle;
      V_Transpose     : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_singular_value_decomposition";

   function Mat_SVD_Back_Substitute
     (Singular_Values : Mat_Handle;
      U               : Mat_Handle;
      V_Transpose     : Mat_Handle;
      Right_Hand_Side : Mat_Handle;
      Result          : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_svd_back_substitute";

   function Mat_Pseudo_Inverse
     (Source : Mat_Handle; Result : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_pseudo_inverse";

   function Mat_Reciprocal_Condition_Number
     (Source : Mat_Handle; Result : access C_Double) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_reciprocal_condition_number";

   function Mat_SVD_Solve_Zero
     (Source : Mat_Handle; Result : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_svd_solve_zero";

   function Mat_Transform
     (Source       : Mat_Handle;
      Coefficients : Mat_Handle;
      Result       : access Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_transform";

   function Mat_Perspective_Transform
     (Source           : Mat_Handle;
      Transform_Matrix : Mat_Handle;
      Result           : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_perspective_transform";

   function Mat_DFT
     (Source         : Mat_Handle;
      Transform_Kind : C_Int32;
      Result         : access Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_dft";

   function Mat_DCT
     (Source         : Mat_Handle;
      Transform_Kind : C_Int32;
      Result         : access Mat_Handle) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_dct";

   function Get_Optimal_DFT_Size
     (Minimum_Size : C_Int32; Result : access C_Int32) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_get_optimal_dft_size";

   function Mat_Multiply_Spectra
     (Left, Right    : Mat_Handle;
      Representation : C_Int32;
      Kind           : C_Int32;
      Result         : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_multiply_spectra";

   function Mat_Mean (Self : Mat_Handle; Result : access Scalar) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_mean";

   function Mat_Mean_Masked
     (Self, Mask : Mat_Handle; Result : access Scalar) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_mean_masked";

   function Mat_Mean_Std_Dev
     (Self               : Mat_Handle;
      Mean               : access Scalar;
      Standard_Deviation : access Scalar) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_mean_std_dev";

   function Mat_Mean_Std_Dev_Masked
     (Self, Mask         : Mat_Handle;
      Mean               : access Scalar;
      Standard_Deviation : access Scalar) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_mean_std_dev_masked";

   function Mat_Norm
     (Self : Mat_Handle; Kind : C_Int32; Result : access C_Double)
      return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_norm";

   function Mat_Norm_Masked
     (Self, Mask : Mat_Handle; Kind : C_Int32; Result : access C_Double)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_norm_masked";

   --  New selectors are independent of the historical Mat_Norm mapping.
   function Mat_Numeric_Norm
     (Self, Mask : Mat_Handle; Kind : C_Int32; Result : access C_Double)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_numeric_norm";

   function Mat_Difference_Norm
     (Left, Right, Mask : Mat_Handle;
      Kind, Relative    : C_Int32;
      Result            : access C_Double) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_difference_norm";

   function Mat_Binary_Norm
     (Self : Mat_Handle; Cell_Bits : C_Int32; Result : access C_Double)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_binary_norm";

   function Mat_Binary_Difference_Norm
     (Left, Right : Mat_Handle; Cell_Bits : C_Int32; Result : access C_Double)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_binary_difference_norm";

   function Mat_PSNR
     (Left, Right : Mat_Handle;
      Peak_Value  : C_Double;
      Result      : access C_Double) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_psnr";

   function Mat_Min_Max_Loc
     (Self      : Mat_Handle;
      Minimum   : access C_Double;
      Maximum   : access C_Double;
      Minimum_X : access C_Int32;
      Minimum_Y : access C_Int32;
      Maximum_X : access C_Int32;
      Maximum_Y : access C_Int32) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_min_max_loc";

   function Mat_Min_Max_Loc_Masked
     (Self, Mask : Mat_Handle;
      Minimum    : access C_Double;
      Maximum    : access C_Double;
      Minimum_X  : access C_Int32;
      Minimum_Y  : access C_Int32;
      Maximum_X  : access C_Int32;
      Maximum_Y  : access C_Int32) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_min_max_loc_masked";

   function Mat_Min_Max_Indices
     (Self             : Mat_Handle;
      Minimum, Maximum : access C_Double;
      Minimum_Indices  : access C_Int32;
      Maximum_Indices  : access C_Int32;
      Capacity         : C_Int32;
      Dimensions       : access C_Int32;
      Has_Minimum      : access C_UInt8;
      Has_Maximum      : access C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_min_max_indices";

   function Mat_Min_Max_Indices_Masked
     (Self, Mask       : Mat_Handle;
      Minimum, Maximum : access C_Double;
      Minimum_Indices  : access C_Int32;
      Maximum_Indices  : access C_Int32;
      Capacity         : C_Int32;
      Dimensions       : access C_Int32;
      Has_Minimum      : access C_UInt8;
      Has_Maximum      : access C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_min_max_indices_masked";

   function Mat_Count_Non_Zero
     (Self : Mat_Handle; Result : access Interfaces.Integer_64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_count_non_zero";
   function Mat_Has_Non_Zero
     (Self : Mat_Handle; Result : access Interfaces.Unsigned_8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_has_non_zero";

   function Mat_Find_Non_Zero
     (Self     : Mat_Handle;
      Points   : access Point;
      Capacity : Interfaces.Integer_64;
      Count    : access Interfaces.Integer_64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_find_non_zero";

   function Mat_Check_Range
     (Source     : Mat_Handle;
      Use_Bounds : C_Boolean;
      Minimum    : C_Double;
      Maximum    : C_Double;
      Valid      : access C_Boolean;
      X          : access C_Int32;
      Y          : access C_Int32) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_check_range";

   function Mat_Patch_NaNs (Self : Mat_Handle; Value : C_Double) return Status
   with Import, Convention => C, External_Name => "opencv_core_mat_patch_nans";

   function Mat_Complete_Symmetry
     (Self : Mat_Handle; Source_Triangle : C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_complete_symmetry";

   function Mat_Set_Identity
     (Self : Mat_Handle; Value : access Scalar) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_mat_set_identity";

   Storage_Mode_Read_Only  : constant C_Int32 := 0;
   Storage_Mode_Write_Only : constant C_Int32 := 1;

   Storage_Format_XML  : constant C_Int32 := 0;
   Storage_Format_YAML : constant C_Int32 := 1;
   Storage_Format_JSON : constant C_Int32 := 2;

   Storage_Structure_Map      : constant C_Int32 := 0;
   Storage_Structure_Sequence : constant C_Int32 := 1;

   Node_Kind_Invalid  : constant C_Int32 := C_Int32 (-1);
   Node_Kind_Integer  : constant C_Int32 := 0;
   Node_Kind_Real     : constant C_Int32 := 1;
   Node_Kind_String   : constant C_Int32 := 2;
   Node_Kind_Sequence : constant C_Int32 := 3;
   Node_Kind_Mapping  : constant C_Int32 := 4;

   function File_Storage_Open
     (Filename : Interfaces.C.char_array;
      Mode     : C_Int32;
      Result   : access File_Storage_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_file_storage_open";

   function File_Storage_Open_Memory_Write
     (Format : C_Int32; Result : access File_Storage_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_file_storage_open_memory_write";

   function File_Storage_Open_Memory_Read
     (Text : Interfaces.C.char_array; Result : access File_Storage_Handle)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_file_storage_open_memory_read";

   function File_Storage_Finish_Memory_Write
     (Self       : File_Storage_Handle;
      Buffer     : System.Address;
      Capacity   : C_UInt64;
      Out_Length : access C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_file_storage_finish_memory_write";

   procedure File_Storage_Destroy (Self : File_Storage_Handle)
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_file_storage_destroy";

   function File_Storage_Write_Mat
     (Self  : File_Storage_Handle;
      Name  : Interfaces.C.char_array;
      Value : Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_file_storage_write_mat";

   function File_Storage_Read_Mat
     (Self   : File_Storage_Handle;
      Name   : Interfaces.C.char_array;
      Result : access Mat_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_file_storage_read_mat";

   function File_Storage_Write_Int
     (Self  : File_Storage_Handle;
      Name  : Interfaces.C.char_array;
      Value : C_Int32) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_file_storage_write_int";

   function File_Storage_Read_Int
     (Self   : File_Storage_Handle;
      Name   : Interfaces.C.char_array;
      Result : access C_Int32) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_file_storage_read_int";

   function File_Storage_Write_Double
     (Self  : File_Storage_Handle;
      Name  : Interfaces.C.char_array;
      Value : C_Double) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_file_storage_write_double";

   function File_Storage_Read_Double
     (Self   : File_Storage_Handle;
      Name   : Interfaces.C.char_array;
      Result : access C_Double) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_file_storage_read_double";

   function File_Storage_Write_String
     (Self  : File_Storage_Handle;
      Name  : Interfaces.C.char_array;
      Value : Interfaces.C.char_array) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_file_storage_write_string";

   function File_Storage_Read_String
     (Self       : File_Storage_Handle;
      Name       : Interfaces.C.char_array;
      Buffer     : System.Address;
      Capacity   : C_UInt64;
      Out_Length : access C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_file_storage_read_string";

   function File_Storage_Begin_Structure
     (Self : File_Storage_Handle;
      Name : Interfaces.C.char_array;
      Kind : C_Int32) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_file_storage_begin_structure";

   function File_Storage_End_Structure
     (Self : File_Storage_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_file_storage_end_structure";

   function File_Storage_Enter_Named_Structure
     (Self : File_Storage_Handle;
      Name : Interfaces.C.char_array;
      Kind : C_Int32) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_file_storage_enter_named_structure";

   function File_Storage_Enter_Indexed_Structure
     (Self : File_Storage_Handle; Index : C_UInt64; Kind : C_Int32)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_file_storage_enter_indexed_structure";

   function File_Storage_Leave_Structure
     (Self : File_Storage_Handle) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_file_storage_leave_structure";

   function File_Storage_Sequence_Length
     (Self : File_Storage_Handle; Out_Length : access C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_file_storage_sequence_length";

   function File_Storage_Map_Length
     (Self : File_Storage_Handle; Out_Length : access C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_file_storage_map_length";

   function File_Storage_Map_Key_At
     (Self       : File_Storage_Handle;
      Index      : C_UInt64;
      Buffer     : System.Address;
      Capacity   : C_UInt64;
      Out_Length : access C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_file_storage_map_key_at";

   function File_Storage_Node_Kind
     (Self   : File_Storage_Handle;
      Name   : Interfaces.C.char_array;
      Result : access C_Int32) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_file_storage_node_kind";

   function File_Storage_Node_Kind_At
     (Self : File_Storage_Handle; Index : C_UInt64; Result : access C_Int32)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_file_storage_node_kind_at";

   function File_Storage_Read_Mat_At
     (Self : File_Storage_Handle; Index : C_UInt64; Result : access Mat_Handle)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_file_storage_read_mat_at";

   function File_Storage_Read_Int_At
     (Self : File_Storage_Handle; Index : C_UInt64; Result : access C_Int32)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_file_storage_read_int_at";

   function File_Storage_Read_Double_At
     (Self : File_Storage_Handle; Index : C_UInt64; Result : access C_Double)
      return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_file_storage_read_double_at";

   function File_Storage_Read_String_At
     (Self       : File_Storage_Handle;
      Index      : C_UInt64;
      Buffer     : System.Address;
      Capacity   : C_UInt64;
      Out_Length : access C_UInt64) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_file_storage_read_string_at";

   --  SparseMat complete-element C2/C3/C4 access. These reuse the dense
   --  vector ABI records; the shim checks exact native depth, channel count
   --  and element size before copying one complete node value. Get and
   --  iterator Next zero the record before any failure.

   --  UInt8 (CV_8UC2/C3/C4)
   function Sparse_Get_UInt8_Vec2
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access UInt8_Vec2) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_get_uint8_vec2";
   function Sparse_Set_UInt8_Vec2
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access constant UInt8_Vec2) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_set_uint8_vec2";
   function Sparse_Iterator_Next_UInt8_Vec2
     (Self    : Sparse_Iterator_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access UInt8_Vec2;
      Found   : access C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_const_iterator_next_uint8_vec2";
   function Sparse_Get_UInt8_Vec3
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access UInt8_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_get_uint8_vec3";
   function Sparse_Set_UInt8_Vec3
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access constant UInt8_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_set_uint8_vec3";
   function Sparse_Iterator_Next_UInt8_Vec3
     (Self    : Sparse_Iterator_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access UInt8_Vec3;
      Found   : access C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_const_iterator_next_uint8_vec3";
   function Sparse_Get_UInt8_Vec4
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access UInt8_Vec4) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_get_uint8_vec4";
   function Sparse_Set_UInt8_Vec4
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access constant UInt8_Vec4) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_set_uint8_vec4";
   function Sparse_Iterator_Next_UInt8_Vec4
     (Self    : Sparse_Iterator_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access UInt8_Vec4;
      Found   : access C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_const_iterator_next_uint8_vec4";

   --  Int8 (CV_8SC2/C3/C4)
   function Sparse_Get_Int8_Vec2
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access Int8_Vec2) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_get_int8_vec2";
   function Sparse_Set_Int8_Vec2
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access constant Int8_Vec2) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_set_int8_vec2";
   function Sparse_Iterator_Next_Int8_Vec2
     (Self    : Sparse_Iterator_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access Int8_Vec2;
      Found   : access C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_const_iterator_next_int8_vec2";
   function Sparse_Get_Int8_Vec3
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access Int8_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_get_int8_vec3";
   function Sparse_Set_Int8_Vec3
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access constant Int8_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_set_int8_vec3";
   function Sparse_Iterator_Next_Int8_Vec3
     (Self    : Sparse_Iterator_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access Int8_Vec3;
      Found   : access C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_const_iterator_next_int8_vec3";
   function Sparse_Get_Int8_Vec4
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access Int8_Vec4) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_get_int8_vec4";
   function Sparse_Set_Int8_Vec4
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access constant Int8_Vec4) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_set_int8_vec4";
   function Sparse_Iterator_Next_Int8_Vec4
     (Self    : Sparse_Iterator_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access Int8_Vec4;
      Found   : access C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_const_iterator_next_int8_vec4";

   --  UInt16 (CV_16UC2/C3/C4)
   function Sparse_Get_UInt16_Vec2
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access UInt16_Vec2) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_get_uint16_vec2";
   function Sparse_Set_UInt16_Vec2
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access constant UInt16_Vec2) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_set_uint16_vec2";
   function Sparse_Iterator_Next_UInt16_Vec2
     (Self    : Sparse_Iterator_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access UInt16_Vec2;
      Found   : access C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_const_iterator_next_uint16_vec2";
   function Sparse_Get_UInt16_Vec3
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access UInt16_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_get_uint16_vec3";
   function Sparse_Set_UInt16_Vec3
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access constant UInt16_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_set_uint16_vec3";
   function Sparse_Iterator_Next_UInt16_Vec3
     (Self    : Sparse_Iterator_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access UInt16_Vec3;
      Found   : access C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_const_iterator_next_uint16_vec3";
   function Sparse_Get_UInt16_Vec4
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access UInt16_Vec4) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_get_uint16_vec4";
   function Sparse_Set_UInt16_Vec4
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access constant UInt16_Vec4) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_set_uint16_vec4";
   function Sparse_Iterator_Next_UInt16_Vec4
     (Self    : Sparse_Iterator_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access UInt16_Vec4;
      Found   : access C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_const_iterator_next_uint16_vec4";

   --  Int16 (CV_16SC2/C3/C4)
   function Sparse_Get_Int16_Vec2
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access Int16_Vec2) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_get_int16_vec2";
   function Sparse_Set_Int16_Vec2
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access constant Int16_Vec2) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_set_int16_vec2";
   function Sparse_Iterator_Next_Int16_Vec2
     (Self    : Sparse_Iterator_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access Int16_Vec2;
      Found   : access C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_const_iterator_next_int16_vec2";
   function Sparse_Get_Int16_Vec3
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access Int16_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_get_int16_vec3";
   function Sparse_Set_Int16_Vec3
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access constant Int16_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_set_int16_vec3";
   function Sparse_Iterator_Next_Int16_Vec3
     (Self    : Sparse_Iterator_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access Int16_Vec3;
      Found   : access C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_const_iterator_next_int16_vec3";
   function Sparse_Get_Int16_Vec4
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access Int16_Vec4) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_get_int16_vec4";
   function Sparse_Set_Int16_Vec4
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access constant Int16_Vec4) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_set_int16_vec4";
   function Sparse_Iterator_Next_Int16_Vec4
     (Self    : Sparse_Iterator_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access Int16_Vec4;
      Found   : access C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_const_iterator_next_int16_vec4";

   --  Int32 (CV_32SC2/C3/C4)
   function Sparse_Get_Int32_Vec2
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access Int32_Vec2) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_get_int32_vec2";
   function Sparse_Set_Int32_Vec2
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access constant Int32_Vec2) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_set_int32_vec2";
   function Sparse_Iterator_Next_Int32_Vec2
     (Self    : Sparse_Iterator_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access Int32_Vec2;
      Found   : access C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_const_iterator_next_int32_vec2";
   function Sparse_Get_Int32_Vec3
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access Int32_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_get_int32_vec3";
   function Sparse_Set_Int32_Vec3
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access constant Int32_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_set_int32_vec3";
   function Sparse_Iterator_Next_Int32_Vec3
     (Self    : Sparse_Iterator_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access Int32_Vec3;
      Found   : access C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_const_iterator_next_int32_vec3";
   function Sparse_Get_Int32_Vec4
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access Int32_Vec4) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_get_int32_vec4";
   function Sparse_Set_Int32_Vec4
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access constant Int32_Vec4) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_set_int32_vec4";
   function Sparse_Iterator_Next_Int32_Vec4
     (Self    : Sparse_Iterator_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access Int32_Vec4;
      Found   : access C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_const_iterator_next_int32_vec4";

   --  Float16 (CV_16FC2/C3/C4): components are raw binary16 encodings.
   function Sparse_Get_Float16_Vec2
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access Float16_Vec2) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_get_float16_vec2";
   function Sparse_Set_Float16_Vec2
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access constant Float16_Vec2) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_set_float16_vec2";
   function Sparse_Iterator_Next_Float16_Vec2
     (Self    : Sparse_Iterator_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access Float16_Vec2;
      Found   : access C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_const_iterator_next_float16_vec2";
   function Sparse_Get_Float16_Vec3
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access Float16_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_get_float16_vec3";
   function Sparse_Set_Float16_Vec3
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access constant Float16_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_set_float16_vec3";
   function Sparse_Iterator_Next_Float16_Vec3
     (Self    : Sparse_Iterator_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access Float16_Vec3;
      Found   : access C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_const_iterator_next_float16_vec3";
   function Sparse_Get_Float16_Vec4
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access Float16_Vec4) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_get_float16_vec4";
   function Sparse_Set_Float16_Vec4
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access constant Float16_Vec4) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_set_float16_vec4";
   function Sparse_Iterator_Next_Float16_Vec4
     (Self    : Sparse_Iterator_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access Float16_Vec4;
      Found   : access C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_const_iterator_next_float16_vec4";

   --  Float32 (CV_32FC2/C3/C4)
   function Sparse_Get_Float32_Vec2
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access Float32_Vec2) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_get_float32_vec2";
   function Sparse_Set_Float32_Vec2
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access constant Float32_Vec2) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_set_float32_vec2";
   function Sparse_Iterator_Next_Float32_Vec2
     (Self    : Sparse_Iterator_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access Float32_Vec2;
      Found   : access C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_const_iterator_next_float32_vec2";
   function Sparse_Get_Float32_Vec3
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access Float32_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_get_float32_vec3";
   function Sparse_Set_Float32_Vec3
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access constant Float32_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_set_float32_vec3";
   function Sparse_Iterator_Next_Float32_Vec3
     (Self    : Sparse_Iterator_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access Float32_Vec3;
      Found   : access C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_const_iterator_next_float32_vec3";
   function Sparse_Get_Float32_Vec4
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access Float32_Vec4) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_get_float32_vec4";
   function Sparse_Set_Float32_Vec4
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access constant Float32_Vec4) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_set_float32_vec4";
   function Sparse_Iterator_Next_Float32_Vec4
     (Self    : Sparse_Iterator_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access Float32_Vec4;
      Found   : access C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_const_iterator_next_float32_vec4";

   --  Float64 (CV_64FC2/C3/C4)
   function Sparse_Get_Float64_Vec2
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access Float64_Vec2) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_get_float64_vec2";
   function Sparse_Set_Float64_Vec2
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access constant Float64_Vec2) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_set_float64_vec2";
   function Sparse_Iterator_Next_Float64_Vec2
     (Self    : Sparse_Iterator_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access Float64_Vec2;
      Found   : access C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_const_iterator_next_float64_vec2";
   function Sparse_Get_Float64_Vec3
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access Float64_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_get_float64_vec3";
   function Sparse_Set_Float64_Vec3
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access constant Float64_Vec3) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_set_float64_vec3";
   function Sparse_Iterator_Next_Float64_Vec3
     (Self    : Sparse_Iterator_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access Float64_Vec3;
      Found   : access C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_const_iterator_next_float64_vec3";
   function Sparse_Get_Float64_Vec4
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access Float64_Vec4) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_get_float64_vec4";
   function Sparse_Set_Float64_Vec4
     (Self    : Sparse_Mat_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access constant Float64_Vec4) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_set_float64_vec4";
   function Sparse_Iterator_Next_Float64_Vec4
     (Self    : Sparse_Iterator_Handle;
      Dims    : C_Int32;
      Indices : access C_Int32;
      Value   : access Float64_Vec4;
      Found   : access C_UInt8) return Status
   with
     Import,
     Convention    => C,
     External_Name => "opencv_core_sparse_const_iterator_next_float64_vec4";

end OpenCV.Internal.C_API;
