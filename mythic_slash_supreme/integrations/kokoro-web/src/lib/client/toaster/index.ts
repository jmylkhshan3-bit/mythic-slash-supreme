declare const Notyf: any;

let notyfInstance: any = null;
function getNotyf(): any {
  if (!notyfInstance) {
    notyfInstance = new Notyf();
  }
  return notyfInstance;
}

const toastCfg = {
  duration: 5000,
  ripple: false,
  position: { x: "right", y: "bottom" },
  dismissible: true,
};

const infiniteToastCfg = {
  ...toastCfg,
  duration: 0,
};

export const toaster = {
  success: (message: string) => {
    getNotyf().open({ type: "success", message, ...toastCfg });
  },
  error: (message: string) => {
    getNotyf().open({ type: "error", message, ...toastCfg });
  },
  successInfinite: (message: string) => {
    getNotyf().open({ type: "success", message, ...infiniteToastCfg });
  },
  errorInfinite: (message: string) => {
    getNotyf().open({ type: "error", message, ...infiniteToastCfg });
  },
};
