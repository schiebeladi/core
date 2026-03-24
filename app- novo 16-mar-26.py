import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import tempfile
import os
from datetime import date, datetime

# --- CONFIGURAÇÃO DA API ---
try:
    if "GEMINI_API_KEY" in st.secrets:
        API_KEY = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-3-flash-preview')
    else:
        st.error("Chave 'GEMINI_API_KEY' não encontrada no Secrets.")
except Exception as e:
    st.error(f"Erro na conexão com a API: {e}")

# --- CONFIGURAÇÕES FIXAS (NATURE VITTA) ---
CONFIG = {
    "logo": "logo.png",
    "historico": "historico_analises.txt",
    "endereco": "Rua Heitor S. de França, 396 CJ 1301",
    "instagram": "@naturevittaoficial",
    "whatsapp": "41 99987-5384",
    "terapeuta_padrao": "Ieda Tissiani Urnau"
}

# --- FUNÇÕES DE SISTEMA ---
def salvar_no_historico(nome_paciente):
    try:
        data_hoje = date.today().strftime("%d-%m-%Y")
        linha = f"{data_hoje}|{nome_paciente}\n"
        with open(CONFIG["historico"], "a", encoding="utf-8") as f:
            f.write(linha)
    except Exception as e:
        st.warning(f"Erro ao salvar histórico: {e}")

def carregar_historico():
    if not os.path.exists(CONFIG["historico"]):
        return []
    with open(CONFIG["historico"], "r", encoding="utf-8") as f:
        return [linha.strip().split("|") for linha in f.readlines()]

def contar_analises_mes():
    historico = carregar_historico()
    mes_atual = date.today().strftime("%m-%Y")
    return sum(1 for item in historico if item[0].startswith(mes_atual))

def limpar_dados():
    for key in ["nome_paciente", "queixa", "analise_atual", "pdf_bytes"]:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state["nascimento"] = date.today()
    st.session_state["sexo"] = "Feminino"
    st.session_state["file_key"] = st.session_state.get("file_key", 0) + 1

# --- CLASSE DO PDF (LAYOUT MINIMALISTA & LIMPO) ---
class RelatorioPDF(FPDF):
    def __init__(self, info_rodape):
        super().__init__()
        self.info_rodape = info_rodape
        self.set_margins(15, 15, 15)

    def header(self):
        if os.path.exists(CONFIG["logo"]):
            self.image(CONFIG["logo"], x=85, y=10, w=40)
            self.ln(35)
        else:
            self.ln(10)

    def footer(self):
        self.set_y(-25)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        contato = f"{self.info_rodape['endereco']} | Instagram: {self.info_rodape['insta']} | Tel: {self.info_rodape['tel']}"
        self.cell(0, 5, contato, align='C', ln=True)
        self.cell(0, 10, f"Página {self.page_no()}", align='C')

def gerar_pdf(texto_analise, dados_usuario, nome_terapeuta, info_rodape):
    pdf = RelatorioPDF(info_rodape)
    pdf.set_auto_page_break(auto=True, margin=25)
    pdf.add_page()
    
    # Cabeçalho do Documento
    pdf.set_font("helvetica", "B", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, "RELATÓRIO DE ANÁLISE INTEGRATIVA", ln=True, align='R')
    data_emissao = date.today().strftime("%d/%m/%Y")
    pdf.cell(0, 5, f"EMITIDO EM: {data_emissao}", ln=True, align='R')
    pdf.ln(2)
    
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, dados_usuario['nome'].upper(), ln=True)
    
    pdf.set_font("helvetica", "", 10)
    info_paciente = f"Nascimento: {dados_usuario['nascimento'].strftime('%d/%m/%Y')} | Idade: {dados_usuario['idade']} anos | Sexo: {dados_usuario['sexo']}"
    pdf.cell(0, 6, info_paciente, ln=True)
    pdf.ln(4)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(8)

    # Parser de Markdown para Hierarquia Visual
    linhas = texto_analise.split('\n')
    for linha in linhas:
        linha = linha.strip()
        if not linha:
            pdf.ln(3)
            continue

        if linha.startswith('# '): # H1
            pdf.ln(2)
            pdf.set_font("helvetica", "B", 14)
            pdf.set_text_color(0, 0, 0)
            pdf.multi_cell(0, 10, linha.replace('# ', '').upper())
            pdf.ln(2)
            
        elif linha.startswith('## '): # H2
            pdf.ln(4)
            pdf.set_font("helvetica", "B", 11)
            pdf.set_text_color(40, 40, 40)
            pdf.multi_cell(0, 8, linha.replace('## ', ''))
            pdf.ln(1)

        elif linha.startswith('### '): # H3
            pdf.set_font("helvetica", "B", 10)
            pdf.set_text_color(80, 80, 80)
            pdf.multi_cell(0, 7, linha.replace('### ', ''))
            
        else: # Texto Normal
            pdf.set_font("helvetica", "", 10)
            pdf.set_text_color(50, 50, 50)
            # Limpeza básica de símbolos de markdown
            texto_limpo = linha.replace('**', '').replace('•', '-').replace('* ', '- ')
            pdf.multi_cell(0, 6, texto_limpo)

    # Assinatura Final
    pdf.ln(15)
    pdf.line(140, pdf.get_y(), 195, pdf.get_y())
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 6, nome_terapeuta, ln=True, align='R')
    pdf.set_font("helvetica", "I", 9)
    pdf.cell(0, 5, "Terapeuta Integrativa", ln=True, align='R')
    
    return pdf.output()

# --- INTERFACE STREAMLIT ---
st.set_page_config(page_title="Nature Vitta - Gestão de Análises", layout="wide")

with st.sidebar:
    st.title("📊 Painel")
    st.metric("Análises este Mês", contar_analises_mes())
    st.divider()
    
    st.subheader("🔍 Histórico Recente")
    hist = carregar_historico()
    if hist:
        for d_item, n_item in reversed(hist[-10:]):
            try:
                st.text(f"📅 {datetime.strptime(d_item, '%d-%m-%Y').strftime('%d/%m/%y')} - {n_item}")
            except: continue
    
    st.divider()
    st.subheader("⚙️ Dados do Cabeçalho")
    nome_terapeuta = st.text_input("Terapeuta", CONFIG["terapeuta_padrao"])
    endereco = st.text_input("Endereço", CONFIG["endereco"])
    insta = st.text_input("Instagram", CONFIG["instagram"])
    tel = st.text_input("WhatsApp", CONFIG["whatsapp"])

st.title("🌿 Portal Nature & Vitta")

c1, c2 = st.columns(2)
with c1:
    st.subheader("📋 Dados do Paciente")
    nome_paciente = st.text_input("Nome Completo", key="nome_paciente")
    nascimento = st.date_input("Data de Nascimento", min_value=date(1900, 1, 1), max_value=date.today(), key="nascimento",format="DD/MM/YYYY")
    sexo = st.selectbox("Sexo", ["Feminino", "Masculino", "Outro"], key="sexo")

with c2:
    st.subheader("📄 Relatório CoRe")
    upload_pdf = st.file_uploader("Anexe o PDF do Inergetix CoRe", type=['pdf'], key=f"pdf_{st.session_state.get('file_key', 0)}")
    queixa = st.text_area("Queixas e Observações", key="queixa")

st.divider()

col_btn1, col_btn2 = st.columns([1, 4])
with col_btn1:
    st.button("🗑️ Limpar Campos", on_click=limpar_dados)
with col_btn2:
    gerar = st.button("🪄 Gerar Relatório Integrativo Profissional")

if gerar:
    if not upload_pdf or not nome_paciente:
        st.warning("Preencha o nome do paciente e anexe o arquivo PDF.")
    else:
        hoje = date.today()
        idade = hoje.year - nascimento.year - ((hoje.month, hoje.day) < (nascimento.month, nascimento.day))

        path_pdf_tmp = None
        try:
            with st.spinner("Analisando frequências e elaborando relatório..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(upload_pdf.getvalue())
                    path_pdf_tmp = tmp.name

                arquivo_gemini = genai.upload_file(path_pdf_tmp)
                
                prompt_final = f"""
                Você é um(a) Terapeuta Integrativo(a) Sênior, com vasta experiência prática em:

                    - Saúde física, emocional, energética e espiritual
                    - Saúde preventiva
                    - Aromaterapia clínica
                    - Nutrição funcional e suplementação
                    - Biorressonância Quântica
                    - Especialista no Sistema Inergetix Core

                    Sua missão é elaborar um relatório integrativo personalizado com base na análise do PDF gerado pelo Inergetix Core para:

                    Paciente: {nome_paciente}  
                    Idade: {idade}  
                    Sexo: {sexo}  
                    Queixa principal: {queixa}

                    ⚠ IMPORTANTE:
                    - A análise NÃO é diagnóstico médico.
                    - Trabalhe com interpretação integrativa e energética.
                    - Utilize linguagem acolhedora, humanizada e profissional.
                    - Escreva como terapeuta experiente, com segurança técnica e sensibilidade.

                    -------------------------------------------------------


                ESTRUTURA OBRIGATÓRIA (Siga exatamente esta ordem e numeração):

                # RELATÓRIO INTEGRATIVO PERSONALIZADO

                    ## 1) Análise Integrativa Simplificada
                    - Analise exclusivamente os óleos e frequências apresentados no PDF.
                    - Explique as possíveis interações energéticas.
                    - Relacione com a idade, sexo e queixa principal do paciente.
                    - Linguagem clara e acessível, sem termos excessivamente técnicos.

                    ## 2) Sua Rotina Diária
                    Elabore uma rotina prática personalizada com:
                    - Uso de óleos por ingestão (quando apropriado)
                    - Inalação
                    - Difusão ambiental
                    - Aplicação tópica

                    Organize em:
                    - Manhã
                    - Tarde
                    - Noite

                    Inclua para cada momento:
                    - Como usar
                    - Quantidade
                    - Forma de uso
                    - Objetivo terapêutico
                    - Uma afirmação positiva personalizada para aquele óleo e aquele momento.

                    ## 3) Seu Guia de Automassagem
                    Crie uma rotina simples e prática de automassagem terapêutica utilizando os óleos indicados.
                    Explique:
                    - Região de aplicação
                    - Movimentos
                    - Frequência
                    - Objetivo energético e emocional

                    ## 4) Rotina de Suplementação (Se houver indicação)
                    Caso faça sentido na análise:
                    - Nome do suplemento
                    - Horário
                    - Quantidade sugerida (de forma orientativa)
                    - Objetivo funcional

                    Nunca prescrever como tratamento médico.

                    ## 5) Suas Recomendações Integrativas
                    Inclua recomendações complementares como:
                    - Hábitos diários
                    - Respiração
                    - Exposição solar
                    - Movimento corporal
                    - Alimentação funcional
                    - Práticas energéticas
                    - Sono
                    - Outros necessárias

                   ## 6) Tempo de Uso e Reavaliação
                        ### Ciclo de 90 dias
                        Explique que este protocolo de óleos, suplementos e práticas deve ser seguido por no máximo 90 dias.
                        ### Importância da Reavaliação
                        Justifique que após 90 dias o corpo processa as informações e o campo energético muda, tornando necessário reavaliar para ajustar o protocolo às novas necessidades celulares e vibracionais.

                    ## 7) Minhas Considerações Finais
                        Texto acolhedor e explicativo reforçando:
                        - A interpretação energética
                        - O papel ativo do paciente no processo
                        - O convite ao autocuidado consciente
                                
                    ## 8) Gotas de Sabedoria
                    Uma dica especial e inédita de aromaterapia para o dia.

                    ## 9) Nota sobre Biorressonância e Autocura
                    Explique de forma simples:
                    - O que é biorressonância quântica (análise de tendências energéticas)
                    - Que não substitui diagnóstico médico
                    - Como os óleos essenciais atuam harmonizando emoções, energia e frequência corporal
                    - Conceito de autocura como processo de equilíbrio interno

                    --

                    REGRAS:
                    - Use '##' para seções principais, '###' para subtópicos, e nunca use negritos (**) para manter o PDF minimalista.
                    - Texto organizado, agradável e fácil de ler.
                    - Parágrafos bem distribuídos.
                    - Tom profissional e empático.
                    - Referencie o texto na voz do(a) terapeuta.

                    Finalize com:
                    Uma mensagem curta de motivação, otimismo e incentivo personalizada para o paciente.
          

                """
                
                response = model.generate_content([prompt_final, arquivo_gemini])
                st.session_state["analise_atual"] = response.text
                
                salvar_no_historico(nome_paciente)
                
                info_rodape = {"endereco": endereco, "insta": insta, "tel": tel}
                st.session_state["pdf_bytes"] = gerar_pdf(
                    response.text, 
                    {"nome": nome_paciente, "nascimento": nascimento, "sexo": sexo, "idade": idade}, 
                    nome_terapeuta, 
                    info_rodape
                )
                st.success("Relatório gerado com sucesso!")
                st.rerun()

        except Exception as e:
            st.error(f"Erro no processamento: {e}")
        finally:
            if path_pdf_tmp and os.path.exists(path_pdf_tmp):
                os.remove(path_pdf_tmp)

if "analise_atual" in st.session_state:
    st.divider()
    st.markdown(st.session_state["analise_atual"])
    st.download_button(
        label="📥 Baixar Relatório Profissional (PDF)",
        data=st.session_state["pdf_bytes"],
        file_name=f"Relatorio_{nome_paciente.replace(' ', '_')}.pdf",
        mime="application/pdf"
    )
