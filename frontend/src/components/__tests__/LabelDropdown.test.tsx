import { render, screen, fireEvent } from "@testing-library/react";
import LabelDropdown from "../LabelDropdown";

describe("LabelDropdown", () => {
  it("renders with default placeholder", () => {
    render(<LabelDropdown onChange={vi.fn()} />);
    expect(screen.getByText("Select character...")).toBeInTheDocument();
  });

  it("shows all Friends characters", () => {
    render(<LabelDropdown onChange={vi.fn()} />);
    expect(screen.getByText("Chandler")).toBeInTheDocument();
    expect(screen.getByText("Joey")).toBeInTheDocument();
    expect(screen.getByText("Monica")).toBeInTheDocument();
    expect(screen.getByText("Rachel")).toBeInTheDocument();
    expect(screen.getByText("Ross")).toBeInTheDocument();
    expect(screen.getByText("Phoebe")).toBeInTheDocument();
    expect(screen.getByText("Other")).toBeInTheDocument();
  });

  it("calls onChange immediately when selecting a character", () => {
    const onChange = vi.fn();
    render(<LabelDropdown onChange={onChange} />);

    const select = screen.getByRole("combobox");
    fireEvent.change(select, { target: { value: "Rachel" } });

    expect(onChange).toHaveBeenCalledWith("Rachel", false);
    expect(onChange).toHaveBeenCalledTimes(1);
  });

  it("shows custom input when Other is selected", () => {
    render(<LabelDropdown onChange={vi.fn()} />);

    const select = screen.getByRole("combobox");
    fireEvent.change(select, { target: { value: "Other" } });

    expect(screen.getByPlaceholderText(/Enter name/)).toBeInTheDocument();
  });

  it("does NOT call onChange on every keystroke", () => {
    const onChange = vi.fn();
    render(<LabelDropdown onChange={onChange} />);

    const select = screen.getByRole("combobox");
    fireEvent.change(select, { target: { value: "Other" } });

    const input = screen.getByPlaceholderText(/Enter name/);
    fireEvent.change(input, { target: { value: "Rachel" } });

    expect(onChange).not.toHaveBeenCalled();
  });

  it("calls onChange on blur with custom label", () => {
    const onChange = vi.fn();
    render(<LabelDropdown onChange={onChange} />);

    const select = screen.getByRole("combobox");
    fireEvent.change(select, { target: { value: "Other" } });

    const input = screen.getByPlaceholderText(/Enter name/);
    fireEvent.change(input, { target: { value: "Rachel" } });
    fireEvent.keyDown(input, { key: "Enter", code: "Enter" });

    expect(onChange).toHaveBeenCalledWith("Rachel", true);
  });

  it("calls onChange on Enter key", () => {
    const onChange = vi.fn();
    render(<LabelDropdown onChange={onChange} />);

    const select = screen.getByRole("combobox");
    fireEvent.change(select, { target: { value: "Other" } });

    const input = screen.getByPlaceholderText(/Enter name/);
    fireEvent.change(input, { target: { value: "Janice" } });
    fireEvent.keyDown(input, { key: "Enter" });

    expect(onChange).toHaveBeenCalledWith("Janice", true);
  });

  it("trims whitespace from custom labels", () => {
    const onChange = vi.fn();
    render(<LabelDropdown onChange={onChange} />);

    const select = screen.getByRole("combobox");
    fireEvent.change(select, { target: { value: "Other" } });

    const input = screen.getByPlaceholderText(/Enter name/);
    fireEvent.change(input, { target: { value: "   Rachel   " } });
    fireEvent.blur(input);

    expect(onChange).toHaveBeenCalledWith("Rachel", true);
  });

  it("does not call onChange if empty", () => {
    const onChange = vi.fn();
    render(<LabelDropdown onChange={onChange} />);

    const select = screen.getByRole("combobox");
    fireEvent.change(select, { target: { value: "Other" } });

    const input = screen.getByPlaceholderText(/Enter name/);
    fireEvent.change(input, { target: { value: "   " } });
    fireEvent.blur(input);

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
