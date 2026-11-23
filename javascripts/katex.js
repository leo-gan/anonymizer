document$.subscribe(({ body }) => {
  if (typeof renderMathInElement === "function") {
    renderMathInElement(body, {
      delimiters: [
        { left: "\\[", right: "\\]", display: true },
        { left: "\\(", right: "\\)", display: false },
      ],
    });
  }
});
