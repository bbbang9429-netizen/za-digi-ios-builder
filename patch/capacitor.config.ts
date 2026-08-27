import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "net.pokerogue.allinone",
  appName: "PokeRogue AIO",
  webDir: "dist",
  server: {
    androidScheme: "https",
  },
};

export default config;
