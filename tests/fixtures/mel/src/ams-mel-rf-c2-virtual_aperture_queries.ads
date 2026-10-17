with AMS.MEL.RF.C2;
package AMS.MEL.RF.C2.Virtual_Aperture_Queries is
   type Status_Kind is (None, Operational, Degraded, Failed);
   function Query_Status (Object : AMS.MEL.RF.C2.Virtual_Aperture) return Status_Kind;
end AMS.MEL.RF.C2.Virtual_Aperture_Queries;
