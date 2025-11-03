clustermark / frontend / src / App.test.tsx;
import { render, screen } from "@testing-library/react";
import App from "./App";

describe("App", () => {
  it("renders the ClusterMark app root", () => {
    render(<App />);
    // Check for a known element or text in your App, adjust as needed
    expect(
      screen.getByText(/ClusterMark|Episode|Upload|Annotate|Friends/i),
    ).toBeInTheDocument();
  });
});
