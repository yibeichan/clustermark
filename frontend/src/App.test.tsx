import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import App from "./App";

describe("App", () => {
  it("renders the ClusterMark app root", () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>,
    );
    // Check for the main heading specifically
    expect(
      screen.getByRole("heading", { name: /ClusterMark/i }),
    ).toBeInTheDocument();
  });
});
