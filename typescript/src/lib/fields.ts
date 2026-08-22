// Shared field-definition engine for FFX / FFX2 save data - a straight
// port of the Python project's fields.py. A FieldDef describes one named
// value inside the save body (numeric fields are little-endian; kind
// "bit" fields pack a single flag into one byte). All offsets are
// relative to the start of the core save body - i.e. after any platform
// header has already been stripped (see saveData.ts, which adds
// headerLen back on for you).

export type FieldKind = "u8" | "u16" | "u32" | "i32" | "f32" | "bit";

export interface FieldDef {
  name: string;
  offset: number;
  kind: FieldKind;
  bit?: number; // only for kind "bit": which bit of the byte at `offset`
  note?: string;
}

function dataViewFor(data: Uint8Array): DataView {
  return new DataView(data.buffer, data.byteOffset, data.byteLength);
}

export function readField(data: Uint8Array, field: FieldDef, headerLen = 0): number | boolean {
  const off = headerLen + field.offset;
  if (field.kind === "bit") {
    return (data[off] & (1 << (field.bit as number))) !== 0;
  }
  const view = dataViewFor(data);
  switch (field.kind) {
    case "u8":
      return view.getUint8(off);
    case "u16":
      return view.getUint16(off, true);
    case "u32":
      return view.getUint32(off, true);
    case "i32":
      return view.getInt32(off, true);
    case "f32":
      return view.getFloat32(off, true);
  }
}

export function writeField(data: Uint8Array, field: FieldDef, value: number | boolean, headerLen = 0): void {
  const off = headerLen + field.offset;
  if (field.kind === "bit") {
    if (value) {
      data[off] |= 1 << (field.bit as number);
    } else {
      data[off] &= ~(1 << (field.bit as number)) & 0xff;
    }
    return;
  }
  const view = dataViewFor(data);
  const num = value as number;
  switch (field.kind) {
    case "u8":
      view.setUint8(off, num);
      break;
    case "u16":
      view.setUint16(off, num, true);
      break;
    case "u32":
      view.setUint32(off, num, true);
      break;
    case "i32":
      view.setInt32(off, num, true);
      break;
    case "f32":
      view.setFloat32(off, num, true);
      break;
  }
}

export function coerceValue(raw: string, kind: FieldKind): number | boolean {
  if (kind === "bit") {
    const s = raw.trim().toLowerCase();
    return s === "1" || s === "true" || s === "yes" || s === "on";
  }
  if (kind === "f32") return parseFloat(raw);
  return parseInt(raw, 10);
}
