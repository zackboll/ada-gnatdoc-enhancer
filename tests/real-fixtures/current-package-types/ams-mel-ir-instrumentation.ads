package AMS.MEL.IR.Instrumentation is
type Priority is (Normal, Debug);
type Instrumentation_Level_Command is record
      Command_ID : Interfaces.Unsigned_32;
      Priority   : Instrumentation.Priority;
   end record;
type Instrumentation_Report is record
      Command_ID   : Interfaces.Unsigned_32;
      Size         : Interfaces.Unsigned_32;
      Timestamp_NS : Long_Long_Integer;
      Priority     : Instrumentation.Priority;
   end record;
end AMS.MEL.IR.Instrumentation;
