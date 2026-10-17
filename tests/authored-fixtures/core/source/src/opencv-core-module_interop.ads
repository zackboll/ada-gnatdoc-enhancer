private with OpenCV.Internal.C_API;

--  Binding implementation interface for cooperating OpenCV Ada module
--  crates. This is not an ordinary application API.
--
--  Each handle is valid only during its callback. A module implementation
--  passes it only to its private C interop layer; it neither owns nor
--  retains the associated native Mat header.

package OpenCV.Core.Module_Interop is

   --  Read-only native Mat handle for cooperating module crates. It is
   --  valid only during the callback that receives it and is neither owned
   --  nor retained by the receiver.
   type Input_Mat_Handle is private;

   --  Writable native Mat handle for cooperating module crates. It exposes
   --  the actual Core header, which an output operation may rebind, and is
   --  valid only during the callback that receives it.
   type Output_Mat_Handle is private;

   --  Invokes Process with an input handle for Image's native header. The
   --  handle is valid only during Process; it must not be stored or used
   --  afterwards. No elements are copied. Exceptions raised by Process
   --  propagate unchanged.
   --  @param Image The Mat whose native header is borrowed.
   --  @param Process Callback that receives the borrowed handle.
   procedure With_Input_Handle
     (Image   : Mat;
      Process : not null access procedure (Handle : Input_Mat_Handle));

   --  Invokes Process with an output handle for Image's actual Core header,
   --  so a native operation may recreate or rebind it in place. The header
   --  is resolved before Process runs; in particular a temporary
   --  external-buffer view is rejected, because its header cannot safely be
   --  rebound by an OutputArray operation. The handle is valid only during
   --  Process and must not be stored or used afterwards. Exceptions raised
   --  by Process propagate unchanged.
   --  @param Image The Mat whose native header is borrowed for writing.
   --  @param Process Callback that receives the borrowed handle.
   --  @exception OpenCV_Error Raised, before Process is invoked, when the
   --  header cannot be used as an output, such as a temporary view.
   procedure With_Output_Handle
     (Image   : in out Mat;
      Process : not null access procedure (Handle : Output_Mat_Handle));

   --  Read-only native UMat handle. UMat handles have the same callback-only
   --  lifetime as the Mat handles. A cooperating module may pass them only to
   --  its private native interop layer. Core owns both the opaque wrapper and
   --  original cv::UMat header: do not delete the header or retain its
   --  pointer after the callback/call scope. No public native pointer
   --  escapes and no ownership transfer, Mat conversion, or mapping occurs.
   --  All module shims must use a compatible OpenCV ABI/installation with
   --  Core.
   type Input_UMat_Handle is private;

   --  Writable native UMat handle with the same callback-only lifetime and
   --  ownership rules as Input_UMat_Handle. It exposes the actual Core-owned
   --  header, which an output operation may rebind.
   type Output_UMat_Handle is private;

   --  Invokes Process with an input handle for Image's native cv::UMat
   --  header. The handle is valid only during Process; it must not be stored,
   --  deleted or used afterwards. No Mat conversion or host mapping occurs.
   --  Exceptions raised by Process propagate unchanged.
   --  @param Image The UMat whose native header is borrowed.
   --  @param Process Callback that receives the borrowed handle.
   procedure With_Input_Handle
     (Image   : UMat;
      Process : not null access procedure (Handle : Input_UMat_Handle));

   --  Invokes Process with an output handle for Image's actual Core-owned
   --  cv::UMat header, which an output operation may rebind. The handle is
   --  valid only during Process; it must not be stored, deleted or used
   --  afterwards. No Mat conversion or host mapping occurs. Exceptions
   --  raised by Process propagate unchanged.
   --  @param Image The UMat whose native header is borrowed for writing.
   --  @param Process Callback that receives the borrowed handle.
   --  @exception OpenCV_Error Raised, before Process is invoked, when the
   --  native header cannot be resolved.
   procedure With_Output_Handle
     (Image   : in out UMat;
      Process : not null access procedure (Handle : Output_UMat_Handle));

private

   type Input_Mat_Handle is new OpenCV.Internal.C_API.Mat_Handle
   with Convention => C;

   type Output_Mat_Handle is new OpenCV.Internal.C_API.Mat_Handle
   with Convention => C;

   type Input_UMat_Handle is new OpenCV.Internal.C_API.UMat_Handle
   with Convention => C;

   type Output_UMat_Handle is new OpenCV.Internal.C_API.UMat_Handle
   with Convention => C;

end OpenCV.Core.Module_Interop;
