from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ...database.database import get_db
from ...core.hierarchy import require_role, RoleEnum
from ...database import models
from ...database.schemas import PacienteCreateSchema, TermoConsentimentoCreateSchema, SaudeGeralCreateSchema, AvaliacaoFototipoCreateSchema


router = APIRouter()

@router.post("/cadastrar-atendimento")
async def cadastrar_atendimento(
    paciente_data: PacienteCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role(RoleEnum.PESQUISADOR))
):

    stmt = select(models.Paciente).filter(models.Paciente.cpf_paciente == paciente_data.cpf_paciente)
    result = await db.execute(stmt)
    existing_paciente = result.scalars().first()

    if not existing_paciente:
        new_paciente = models.Paciente(
            nome_paciente=paciente_data.nome_paciente,
            data_nascimento=paciente_data.data_nascimento,
            sexo=paciente_data.sexo,
            sexo_outro=paciente_data.sexo_outro,
            cpf_paciente=paciente_data.cpf_paciente,
            num_cartao_sus=paciente_data.num_cartao_sus,
            endereco_paciente=paciente_data.endereco_paciente,
            telefone_paciente=paciente_data.telefone_paciente,
            email_paciente=paciente_data.email_paciente,
            autoriza_pesquisa=paciente_data.autoriza_pesquisa,
            id_usuario_criacao=current_user.id
        )
        db.add(new_paciente)
        await db.commit()
        await db.refresh(new_paciente)
    else:
        raise HTTPException(status_code=400, detail="Paciente já cadastrado")
        

    new_atendimento = models.Atendimento(
        paciente_id=new_paciente.id,
        user_id=current_user.id
    )

    db.add(new_atendimento)
    await db.commit()
    await db.refresh(new_atendimento)

    return new_atendimento


@router.post("/cadastrar-termo-consentimento")
async def cadastrar_termo_consentimento(
    termo_data: TermoConsentimentoCreateSchema,
    atendimento_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role(RoleEnum.PESQUISADOR))
):

    stmt = select(models.Atendimento).filter(models.Atendimento.id == atendimento_id)
    result = await db.execute(stmt)
    atendimento = result.scalars().first()

    if not atendimento:
        raise HTTPException(status_code=404, detail="Atendimento não encontrado")
    
    if atendimento.termo_consentimento_id:
        raise HTTPException(status_code=400, detail="Atendimento já possui um termo de consentimento")

    new_termo = models.TermoConsentimento(
        arquivo_url=termo_data.arquivo_url
    )

    db.add(new_termo)
    await db.commit()
    await db.refresh(new_termo)

    atendimento.termo_consentimento_id = new_termo.id
    await db.commit()
    await db.refresh(atendimento)

    return {
        "message": "Termo de Consentimento cadastrado com sucesso!",
        "termo_consentimento": new_termo
    }

@router.post("/cadastrar-saude-geral")
async def cadastrar_saude_geral(
    saude_geral_data: SaudeGeralCreateSchema,
    atendimento_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role(RoleEnum.PESQUISADOR))
):
    stmt = select(models.Atendimento).filter(models.Atendimento.id == atendimento_id)
    result = await db.execute(stmt)
    atendimento = result.scalars().first()

    if not atendimento:
        raise HTTPException(status_code=404, detail="Atendimento não encontrado")
    
    if atendimento.saude_geral_id:
        raise HTTPException(status_code=400, detail="Atendimento já possui informações de Saúde Geral")

    new_saude_geral = models.SaudeGeral(
        doencas_cronicas=saude_geral_data.doencas_cronicas,
        hipertenso=saude_geral_data.hipertenso,
        diabetes=saude_geral_data.diabetes,
        cardiopatia=saude_geral_data.cardiopatia,
        outras_doencas=saude_geral_data.outras_doencas,
        diagnostico_cancer=saude_geral_data.diagnostico_cancer,
        tipo_cancer=saude_geral_data.tipo_cancer,
        uso_medicamentos=saude_geral_data.uso_medicamentos,
        medicamentos=saude_geral_data.medicamentos,
        possui_alergia=saude_geral_data.possui_alergia,
        alergias=saude_geral_data.alergias,
        ciruturgias_dermatologicas=saude_geral_data.ciruturgias_dermatologicas,
        tipo_procedimento=saude_geral_data.tipo_procedimento,
        pratica_atividade_fisica=saude_geral_data.pratica_atividade_fisica,
        frequencia_atividade_fisica=saude_geral_data.frequencia_atividade_fisica
    )

    db.add(new_saude_geral)
    await db.commit()
    await db.refresh(new_saude_geral)

    atendimento.saude_geral_id = new_saude_geral.id
    await db.commit()
    await db.refresh(atendimento)

    return {
        "message": "Informações de Saúde Geral cadastradas com sucesso!",
        "saude_geral": new_saude_geral
    }

@router.post("/cadastrar-avaliacao-fototipo")
async def cadastrar_avaliacao_fototipo(
    fototipo_data: AvaliacaoFototipoCreateSchema,
    atendimento_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role(RoleEnum.PESQUISADOR))
):
    
    valid_cor_pele = [0, 2, 4, 8, 12, 16, 20]
    valid_cor_olhos = [0, 1, 2, 3, 4]
    valid_cor_cabelo = [0, 1, 2, 3, 4]
    valid_quantidade_sardas = [0, 1, 2, 3]
    valid_reacao_sol = [0, 2, 4, 6, 8]
    valid_bronzeamento = [0, 2, 4, 6]
    valid_sensibilidade_solar = [0, 1, 2, 3, 4]

    if fototipo_data.cor_pele not in valid_cor_pele:
        raise HTTPException(status_code=400, detail="Valor inválido para cor_pele")
    if fototipo_data.cor_olhos not in valid_cor_olhos:
        raise HTTPException(status_code=400, detail="Valor inválido para cor_olhos")
    if fototipo_data.cor_cabelo not in valid_cor_cabelo:
        raise HTTPException(status_code=400, detail="Valor inválido para cor_cabelo")
    if fototipo_data.quantidade_sardas not in valid_quantidade_sardas:
        raise HTTPException(status_code=400, detail="Valor inválido para quantidade_sardas")
    if fototipo_data.reacao_sol not in valid_reacao_sol:
        raise HTTPException(status_code=400, detail="Valor inválido para reacao_sol")
    if fototipo_data.bronzeamento not in valid_bronzeamento:
        raise HTTPException(status_code=400, detail="Valor inválido para bronzeamento")
    if fototipo_data.sensibilidade_solar not in valid_sensibilidade_solar:
        raise HTTPException(status_code=400, detail="Valor inválido para sensibilidade_solar")


    stmt = select(models.Atendimento).filter(models.Atendimento.id == atendimento_id)
    result = await db.execute(stmt)
    atendimento = result.scalars().first()

    if not atendimento:
        raise HTTPException(status_code=404, detail="Atendimento não encontrado")
    
    if atendimento.avaliacao_fototipo_id:
        raise HTTPException(status_code=400, detail="Atendimento já possui uma avaliação de fototipo")

    new_fototipo = models.AvaliacaoFototipo(
        cor_pele=fototipo_data.cor_pele,
        cor_olhos=fototipo_data.cor_olhos,
        cor_cabelo=fototipo_data.cor_cabelo,
        quantidade_sardas=fototipo_data.quantidade_sardas,
        reacao_sol=fototipo_data.reacao_sol,
        bronzeamento=fototipo_data.bronzeamento,
        sensibilidade_solar=fototipo_data.sensibilidade_solar
    )

    db.add(new_fototipo)
    await db.commit()
    await db.refresh(new_fototipo)

    atendimento.avaliacao_fototipo_id = new_fototipo.id
    await db.commit()
    await db.refresh(atendimento)

    return {
        "message": "Avaliação de Fototipo cadastrada com sucesso!",
        "avaliacao_fototipo": new_fototipo
    }

@router.get("/listar-atendimentos-usuario-logado")
async def listar_atendimentos_usuario_logado(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role(RoleEnum.PESQUISADOR))
):

    stmt = (
        select(models.Atendimento, models.Paciente.nome_paciente, models.Paciente.cpf_paciente)
        .join(models.Paciente, models.Atendimento.paciente_id == models.Paciente.id)
        .filter(models.Atendimento.user_id == current_user.id)
    )
    
    result = await db.execute(stmt)
    atendimentos = result.all()

    if not atendimentos:
        raise HTTPException(status_code=404, detail="Nenhum atendimento encontrado para este usuário.")

    atendimentos_list = [
        {
            "id": atendimento.Atendimento.id,
            "data_atendimento": atendimento.Atendimento.data_atendimento,
            "paciente_id": atendimento.Atendimento.paciente_id,
            "nome_paciente": atendimento.nome_paciente,
            "cpf_paciente": atendimento.cpf_paciente,
            "termo_consentimento_id": atendimento.Atendimento.termo_consentimento_id,
            "saude_geral_id": atendimento.Atendimento.saude_geral_id,
            "avaliacao_fototipo_id": atendimento.Atendimento.avaliacao_fototipo_id
        }
        for atendimento in atendimentos
    ]

    return atendimentos_list