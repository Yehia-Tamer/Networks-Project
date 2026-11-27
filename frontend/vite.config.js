import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// host: true -> listen on the laptop's Wi-Fi IP too, so phones on the same network can open it.
export default defineConfig({
  plugins: [react()],
  server: { host: true, port: 5173, strictPort: true },
});
