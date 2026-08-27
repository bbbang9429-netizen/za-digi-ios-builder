import { UiMode } from "#enums/ui-mode";
import type { PlayerPokemon } from "#field/pokemon";
import type { OptionSelectItem } from "#ui/abstract-option-select-ui-handler";
import type { InputFieldConfig } from "#ui/form-modal-ui-handler";
import { FormModalUiHandler } from "#ui/form-modal-ui-handler";
import type { ModalConfig } from "#ui/modal-ui-handler";
import i18next from "i18next";

interface RenameAutocompleteConfig extends ModalConfig {
  /** Optional live autocomplete provider used by the offline starter editor. */
  autocompleteValues?: (query: string) => string[];
  autocompleteMaxOptions?: number;
}

export class RenameFormUiHandler extends FormModalUiHandler {
  private autocompleteInput?: any;
  private autocompleteListener?: (...args: any[]) => void;
  private suppressAutocomplete = false;

  getModalTitle(_config?: ModalConfig): string {
    return i18next.t("menu:renamePokemon");
  }

  getWidth(_config?: ModalConfig): number {
    return 160;
  }

  getMargin(_config?: ModalConfig): [number, number, number, number] {
    return [0, 0, 48, 0];
  }

  getButtonLabels(_config?: ModalConfig): string[] {
    return [i18next.t("menu:rename"), i18next.t("menu:cancel")];
  }

  getReadableErrorMessage(error: string): string {
    const colonIndex = error?.indexOf(":");
    if (colonIndex > 0) {
      error = error.slice(0, colonIndex);
    }

    return super.getReadableErrorMessage(error);
  }

  override getInputFieldConfigs(): InputFieldConfig[] {
    return [{ label: i18next.t("menu:nickname") }];
  }

  show(args: any[]): boolean {
    if (super.show(args)) {
      const config = args[0] as RenameAutocompleteConfig;
      const ui = this.getUi();
      const input = this.inputs[0];

      // Remove the listener installed by a previous use of this persistent modal.
      if (this.autocompleteInput && this.autocompleteListener) {
        this.autocompleteInput.off("textchange", this.autocompleteListener);
      }
      this.autocompleteInput = undefined;
      this.autocompleteListener = undefined;
      this.suppressAutocomplete = false;

      // TODO: shouldn't this be `const playerPokemon: PlayerPokemon | undefined = args[1];` and `if (playerPokemon)`?
      if (args[1] && typeof (args[1] as PlayerPokemon).getNameToRender === "function") {
        input.text = (args[1] as PlayerPokemon).getNameToRender({ useIllusion: false });
      } else {
        input.text = args[1];
      }

      if (config.autocompleteValues) {
        const autocompleteListener = (inputObject: any) => {
          if (this.suppressAutocomplete) {
            return;
          }

          // Replace the previous suggestion window on every insertion/deletion.
          if (ui.getMode() === UiMode.AUTO_COMPLETE) {
            ui.revertMode();
          }

          const query = String(inputObject.text ?? "").trim();
          if (!query) {
            return;
          }

          const values = config.autocompleteValues?.(query) ?? [];
          if (!values.length) {
            return;
          }

          const options: OptionSelectItem[] = values.map(value => ({
            label: value,
            handler: () => {
              // Selecting a suggestion fills the search field; the user can then confirm normally.
              this.suppressAutocomplete = true;
              inputObject.setText(value);
              if (ui.getMode() === UiMode.AUTO_COMPLETE) {
                ui.revertMode();
              }
              this.suppressAutocomplete = false;
              setTimeout(() => inputObject.node?.focus?.(), 0);
              return true;
            },
          }));

          ui.setOverlayMode(UiMode.AUTO_COMPLETE, {
            options,
            maxOptions: config.autocompleteMaxOptions ?? 5,
            modalContainer: this.modalContainer,
          });
        };

        this.autocompleteInput = input;
        this.autocompleteListener = autocompleteListener;
        input.on("textchange", autocompleteListener);
      }

      this.submitAction = () => {
        this.sanitizeInputs();
        const sanitizedName = btoa(unescape(encodeURIComponent(input.text)));

        // Search mode reuses the rename form. Hide the form immediately before handing
        // control back to the starter editor so an async mode transition cannot leave the
        // nickname window (and its native text input) visible over the starter screen.
        input.node?.blur?.();
        this.hide();
        config.buttonActions[0](sanitizedName);
        return true;
      };

      const configuredCancelAction = config.buttonActions[1];
      this.cancelAction = () => {
        input.node?.blur?.();
        this.hide();
        configuredCancelAction?.();
      };
      return true;
    }
    return false;
  }

  override clear(): void {
    if (this.autocompleteInput && this.autocompleteListener) {
      this.autocompleteInput.off("textchange", this.autocompleteListener);
    }
    this.autocompleteInput = undefined;
    this.autocompleteListener = undefined;
    this.suppressAutocomplete = false;
    super.clear();
  }
}
