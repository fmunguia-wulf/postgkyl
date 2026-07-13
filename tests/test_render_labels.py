"""Tests for postgkyl.render.labels — latex_to_unicode / latex_to_html."""

from __future__ import annotations

from postgkyl.render.labels import latex_to_html, latex_to_unicode


class TestLatexToUnicode:
  def test_empty_string_passthrough(self):
    assert latex_to_unicode("") == ""
  # end

  def test_plain_text_unchanged(self):
    assert latex_to_unicode("hello") == "hello"
  # end

  def test_strips_dollar_delimiters(self):
    assert latex_to_unicode(r"$\mu$") == "μ"
  # end

  def test_greek_letter_without_dollars(self):
    assert latex_to_unicode(r"\rho") == "ρ"
  # end

  def test_multiple_greek_letters(self):
    assert latex_to_unicode(r"\alpha \beta \gamma") == "α β γ"
  # end

  def test_uppercase_greek_letters(self):
    assert latex_to_unicode(r"\Omega \Delta \Theta \Sigma \Lambda") == "Ω Δ Θ Σ Λ"
  # end

  def test_parallel_and_perp_with_subscripts_unconverted(self):
    assert latex_to_unicode(r"$\mu_{\parallel}$") == "μ_{∥}"
    assert latex_to_unicode(r"E_{\perp}") == "E_{⊥}"
  # end

  def test_strips_surrounding_whitespace(self):
    assert latex_to_unicode("  \\pi  ") == "π"
  # end
# end


class TestLatexToHtml:
  def test_empty_string_passthrough(self):
    assert latex_to_html("") == ""
  # end

  def test_plain_text_unchanged(self):
    result = latex_to_html("field")
    assert result == "field"
  # end

  def test_brace_subscript_becomes_html_sub(self):
    result = latex_to_html(r"$B_{x}$")
    assert result == "B<sub>x</sub>"
  # end

  def test_bare_subscript_becomes_html_sub(self):
    result = latex_to_html("n_0")
    assert result == "n<sub>0</sub>"
  # end

  def test_greek_letter_converted(self):
    result = latex_to_html(r"$\omega$")
    assert "ω" in result
  # end

  def test_greek_and_subscript_combined(self):
    assert latex_to_html(r"$\mu_{\parallel}$") == "μ<sub>∥</sub>"
    assert latex_to_html(r"E_{\perp}") == "E<sub>⊥</sub>"
  # end
# end
