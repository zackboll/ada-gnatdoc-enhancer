private with OpenCV.Internal.C_API;

--  Binding implementation interface for cooperating OpenCV Ada module
--  crates. This is not an ordinary application API.
--
--  Each handle is valid only during its callback. A module implementation
--  passes it only to its private C interop layer; it neither owns nor
--  retains the associated native SparseMat header, and it does not copy
--  node storage. There is no temporary external-buffer SparseMat view.
--  Output handles expose the actual Core header so an operation such as
--  calcHist can call SparseMat::create on it in place.

package OpenCV.Core.Sparse.Module_Interop is

   --  Read-only native SparseMat handle for cooperating module crates. It
   --  is valid only during the callback that receives it and is neither
   --  owned nor retained by the receiver.
   type Input_Sparse_Mat_Handle is private;

   --  Writable native SparseMat handle for cooperating module crates. It
   --  exposes the actual Core header and is valid only during the callback
   --  that receives it; the receiver neither owns nor retains it.
   type Output_Sparse_Mat_Handle is private;

   --  Invokes Process with an input handle for Image's native header. The
   --  handle is valid only during Process; it must not be stored or used
   --  afterwards. No node storage is copied. Exceptions raised by Process
   --  propagate unchanged.
   --  @param Image The Sparse_Mat whose native header is borrowed.
   --  @param Process Callback that receives the borrowed handle.
   procedure With_Input_Handle
     (Image   : Sparse_Mat;
      Process : not null access procedure (Handle : Input_Sparse_Mat_Handle));

   --  Invokes Process with an output handle for Image's actual Core header,
   --  so an operation such as calcHist can call SparseMat::create on it in
   --  place. The header is resolved before Process runs, so an invalid Core
   --  header is rejected without invoking the callback. The handle is valid
   --  only during Process and must not be stored or used afterwards. There
   --  is no temporary external-buffer SparseMat view to reject. Exceptions
   --  raised by Process propagate unchanged.
   --  @param Image The Sparse_Mat whose native header is borrowed for
   --  writing.
   --  @param Process Callback that receives the borrowed handle.
   --  @exception OpenCV_Error Raised, before Process is invoked, when the
   --  native header cannot be resolved.
   procedure With_Output_Handle
     (Image   : in out Sparse_Mat;
      Process : not null access procedure (Handle : Output_Sparse_Mat_Handle));

private

   type Input_Sparse_Mat_Handle is new OpenCV.Internal.C_API.Sparse_Mat_Handle
   with Convention => C;

   type Output_Sparse_Mat_Handle is new OpenCV.Internal.C_API.Sparse_Mat_Handle
   with Convention => C;

end OpenCV.Core.Sparse.Module_Interop;
