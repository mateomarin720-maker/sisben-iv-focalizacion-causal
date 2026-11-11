"""El anexo de trazabilidad lee cada cifra de su reporte en `docs/reports/`
(versionados): si un reporte cambia de formato o una cifra desaparece, el
generador falla y esta prueba lo detecta."""
from src.utils import anexo_trazabilidad as at


def test_cada_cifra_sale_de_su_reporte():
    c = at.cifras(contar_pruebas=False)
    assert len(c) > 40
    assert all(x.valor and (at.R / x.archivo).exists() or x.archivo.startswith(("tests", "src")) for x in c)
    # toda cifra simulada lleva asterisco; ninguna real
    for x in c:
        assert (r"\*" in x.valor) == (x.simulada and "Repeticiones" not in x.que), x.que


def test_formato_con_coma_decimal():
    assert at.num(-0.0026, 4, signo=True) == "−0,0026"
    assert at.num(0.4359, 1, pct=True) == "43,6 %"
    assert at.num(290968, 0) == "290.968"
