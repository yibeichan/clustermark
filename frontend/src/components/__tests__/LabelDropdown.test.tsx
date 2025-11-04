import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import LabelDropdown from "../LabelDropdown";

describe("LabelDropdown", () => {
  it("renders with default placeholder", () => {
    render(<LabelDropdown onChange={vi.fn()} />);
    expect(screen.getByText("Select character...")).toBeInTheDocument();
  });

  it("shows all Friends characters", () => {
    render(<LabelDropdown onChange={vi.fn()} />);
    const characters = [
      "Chandler",
      "Joey",
      "Monica",
      "Rachel",
      "Ross",
      "Phoebe",
      "Other",
    ];
    for (const character of characters) {
      expect(screen.getByText(character)).toBeInTheDocument();
    }
  });

  it("calls onChange immediately when selecting a character", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<LabelDropdown onChange={onChange} />);

    const select = screen.getByRole("combobox");
    await user.selectOptions(select, "Rachel");

    expect(onChange).toHaveBeenCalledWith("Rachel", false);
    expect(onChange).toHaveBeenCalledTimes(1);
  });

  it("shows custom input when Other is selected", async () => {
    const user = userEvent.setup();
    render(<LabelDropdown onChange={vi.fn()} />);

    const select = screen.getByRole("combobox");
    await user.selectOptions(select, "Other");

    expect(screen.getByPlaceholderText(/Enter name/)).toBeInTheDocument();
  });

  it("does NOT call onChange on every keystroke", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<LabelDropdown onChange={onChange} />);

    const select = screen.getByRole("combobox");
    await user.selectOptions(select, "Other");

    const input = screen.getByPlaceholderText(/Enter name/);
    await user.type(input, "Rachel");

    expect(onChange).not.toHaveBeenCalled();
  });

  it("calls onChange on blur with custom label", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<LabelDropdown onChange={onChange} />);

    const select = screen.getByRole("combobox");
    await user.selectOptions(select, "Other");

    const input = screen.getByPlaceholderText(/Enter name/);
    await user.type(input, "Rachel");
    await user.tab(); // tab away to trigger blur

    expect(onChange).toHaveBeenCalledWith("Rachel", true);
  });

  it("calls onChange on Enter key", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<LabelDropdown onChange={onChange} />);

    const select = screen.getByRole("combobox");
    await user.selectOptions(select, "Other");

    const input = screen.getByPlaceholderText(/Enter name/);
    await user.type(input, "Janice{Enter}");

    expect(onChange).toHaveBeenCalledWith("Janice", true);
  });

  it("trims whitespace from custom labels", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<LabelDropdown onChange={onChange} />);

    const select = screen.getByRole("combobox");
    await user.selectOptions(select, "Other");

    const input = screen.getByPlaceholderText(/Enter name/);
    await user.type(input, "   Rachel   ");
    await user.tab(); // tab away to trigger blur

    expect(onChange).toHaveBeenCalledWith("Rachel", true);
  });

  it("does not call onChange if empty", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<LabelDropdown onChange={onChange} />);

    const select = screen.getByRole("combobox");
    await user.selectOptions(select, "Other");

    const input = screen.getByPlaceholderText(/Enter name/);
    await user.type(input, "   ");
    await user.tab(); // tab away to trigger blur

    expect(onChange).not.toHaveBeenCalled();
  });

  it("initializes with predefined character", () => {
    render(<LabelDropdown onChange={vi.fn()} value="Monica" />);

    const select = screen.getByRole("combobox") as HTMLSelectElement;
    expect(select.value).toBe("Monica");
  });

  it("initializes with custom value", () => {
    render(<LabelDropdown onChange={vi.fn()} value="Gunther" />);

    const select = screen.getByRole("combobox") as HTMLSelectElement;
    expect(select.value).toBe("Other");
    expect(screen.getByDisplayValue("Gunther")).toBeInTheDocument();

    const input = screen.getByPlaceholderText(/Enter name/) as HTMLInputElement;
    expect(input.value).toBe("Gunther");
  });

  it("disables when disabled prop is true", () => {
    render(<LabelDropdown onChange={vi.fn()} disabled />);

    const select = screen.getByRole("combobox");
    expect(select).toBeDisabled();
  });
});
