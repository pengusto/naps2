using System.Reflection.Metadata;
using System.Reflection.PortableExecutable;
using System.Text.Json;
var result = new List<object>();
foreach (var path in Directory.EnumerateFiles(args[0], "*.dll")) {
 using var input = File.OpenRead(path); using var pe = new PEReader(input);
 if (!pe.HasMetadata) continue;
 var reader = pe.GetMetadataReader(); var asm = reader.GetAssemblyDefinition();
 var attrs = new Dictionary<string,string>();
 foreach (var h in asm.GetCustomAttributes()) {
  var a = reader.GetCustomAttribute(h); EntityHandle type;
  if (a.Constructor.Kind == HandleKind.MemberReference) type = reader.GetMemberReference((MemberReferenceHandle)a.Constructor).Parent;
  else if (a.Constructor.Kind == HandleKind.MethodDefinition) type = reader.GetMethodDefinition((MethodDefinitionHandle)a.Constructor).GetDeclaringType();
  else continue;
  string name = type.Kind == HandleKind.TypeReference ? reader.GetString(reader.GetTypeReference((TypeReferenceHandle)type).Name) : type.Kind == HandleKind.TypeDefinition ? reader.GetString(reader.GetTypeDefinition((TypeDefinitionHandle)type).Name) : "";
  if (!new[]{"AssemblyInformationalVersionAttribute","AssemblyFileVersionAttribute","AssemblyCopyrightAttribute","AssemblyCompanyAttribute","AssemblyProductAttribute"}.Contains(name)) continue;
  try { var b = reader.GetBlobReader(a.Value); if(b.ReadUInt16()==1) attrs[name] = b.ReadSerializedString() ?? ""; } catch(BadImageFormatException) {}
 }
 result.Add(new { file = Path.GetFileName(path), name=reader.GetString(asm.Name), version=asm.Version.ToString(), attributes=attrs,
 references=reader.AssemblyReferences.Select(h => reader.GetString(reader.GetAssemblyReference(h).Name)).ToArray() });
}
Console.WriteLine(JsonSerializer.Serialize(result, new JsonSerializerOptions {WriteIndented=true}));
