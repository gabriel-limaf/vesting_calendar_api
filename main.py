# uvicorn main:app --reload
# abrir local para testar a API http://localhost:8000/docs

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
from dateutil.relativedelta import relativedelta
import math


app = FastAPI()


class VestingParams(BaseModel):
    total_acoes: int = Field(
        ...,
        description=(
            "Quantidade total de ações disponíveis para o incentivo de longo prazo"
        )
    )
    vesting: int = Field(
        ...,
        description=(
            "Informar o total de meses de vesting"
        )
    )
    cliff: int = Field(
        ...,
        description=(
            "Período inicial em que nenhum direito sobre as ações é adquirido"
        )
    )
    periodicidade: int = Field(
        ...,
        description=(
            "Frequência com que o direito sobre as ações é adquirido após o cliff"
        )
    )
    data_inicio_vesting: datetime = Field(
        ...,
        description=(
            "Informar qual a data de inicio do vesting"
        )
    )
    arredondamento: int = Field(
        ...,
        description=(
            "Define a forma de arredondamento a ser utilizada. Aceita números de 1 a 7:<br>"
            "1: Cumulative Rounding (5 - 4 - 5 - 4)<br>"
            "2: Cumulative Round Down (4 - 5 - 4 - 5)<br>"
            "3: Front Loaded (5 - 5 - 4 - 4)<br>"
            "4: Back Loaded (4 - 4 - 5 - 5)<br>"
            "5: Front Loaded to Single Tranche (6 - 4 - 4 - 4)<br>"
            "6: Back Loaded to Single Tranche (4 - 4 - 4 - 6)<br>"
            "7: Fractional (4.5 - 4.5 - 4.5 - 4.5)<br>"
        )
    )


def gerar_datas_vesting(data_inicio, quantidade_tranches, intervalo_meses):
    datas = []
    for i in range(1, quantidade_tranches + 1):
        data_futura = data_inicio + relativedelta(months=i * intervalo_meses)
        datas.append(data_futura.strftime('%Y-%m-%d'))
    return datas


def cumulative_rounding(total_acoes, tranche_sem_cliff, tranches_no_cliff):
    lista_acoes_na_tranche = []
    acumulado = []
    for _ in range(tranche_sem_cliff):
        acoes_na_tranche = total_acoes / tranche_sem_cliff
        lista_acoes_na_tranche.append(acoes_na_tranche)
    accumulator = 0
    for item in lista_acoes_na_tranche:
        accumulator += item
        acumulado.append(math.ceil(accumulator))
    diff_list = [acumulado[i] - acumulado[i - 1] if i > 0 else acumulado[0] for i in range(len(acumulado))]
    soma_acoes_no_cliff = sum(diff_list[:tranches_no_cliff])
    nova_lista = [soma_acoes_no_cliff] + diff_list[tranches_no_cliff:]
    return nova_lista


def cumulative_rounding_down(total_acoes, tranche_sem_cliff, tranches_no_cliff):
    lista_acoes_na_tranche = []
    acumulado = []
    for _ in range(tranche_sem_cliff):
        acoes_na_tranche = total_acoes / tranche_sem_cliff
        lista_acoes_na_tranche.append(acoes_na_tranche)
    accumulator = 0
    for item in lista_acoes_na_tranche:
        accumulator += item
        acumulado.append(math.floor(accumulator))
    diff_list = [acumulado[i] - acumulado[i - 1] if i > 0 else acumulado[0] for i in range(len(acumulado))]
    soma_acoes_no_cliff = sum(diff_list[:tranches_no_cliff])
    nova_lista = [soma_acoes_no_cliff] + diff_list[tranches_no_cliff:]
    return nova_lista


def front_loaded(total_acoes, tranche_sem_cliff, tranches_no_cliff):
    lista_acoes_na_tranche = []
    for _ in range(tranche_sem_cliff):
        acoes_na_tranche = math.floor(total_acoes / tranche_sem_cliff)
        lista_acoes_na_tranche.append(acoes_na_tranche)
    sobra = total_acoes - sum(lista_acoes_na_tranche)
    idx = 0
    while sobra > 0:
        lista_acoes_na_tranche[idx] += 1
        sobra -= 1
        idx += 1
        if idx >= tranche_sem_cliff:
            idx = 0
    soma_acoes_no_cliff = sum(lista_acoes_na_tranche[:tranches_no_cliff])
    nova_lista = [soma_acoes_no_cliff] + lista_acoes_na_tranche[tranches_no_cliff:]
    return nova_lista


def back_loaded(total_acoes, tranche_sem_cliff, tranches_no_cliff, cliff):
    lista_acoes_na_tranche = []
    for _ in range(tranche_sem_cliff):
        acoes_na_tranche = math.floor(total_acoes / tranche_sem_cliff)
        lista_acoes_na_tranche.append(acoes_na_tranche)
    sobra = total_acoes - sum(lista_acoes_na_tranche)
    idx = len(lista_acoes_na_tranche) - 1
    while sobra > 0:
        lista_acoes_na_tranche[idx] += 1
        sobra -= 1
        idx -= 1
        if idx < cliff:
            idx = len(lista_acoes_na_tranche) - 1
    soma_acoes_no_cliff = sum(lista_acoes_na_tranche[:tranches_no_cliff])
    nova_lista = [soma_acoes_no_cliff] + lista_acoes_na_tranche[tranches_no_cliff:]
    return nova_lista


def front_loaded_to_single_tranche(total_acoes, tranche_sem_cliff, tranches_no_cliff, acoes_restantes):
    lista_acoes_na_tranche = []
    for _ in range(tranche_sem_cliff):
        acoes_na_tranche = math.floor(total_acoes / tranche_sem_cliff)
        lista_acoes_na_tranche.append(acoes_na_tranche)
    lista_acoes_na_tranche[0] += acoes_restantes
    soma_acoes_no_cliff = sum(lista_acoes_na_tranche[:tranches_no_cliff])
    nova_lista = [soma_acoes_no_cliff] + lista_acoes_na_tranche[tranches_no_cliff:]
    return nova_lista


def back_loaded_to_single_tranche(total_acoes, tranche_sem_cliff, tranches_no_cliff, acoes_restantes):
    lista_acoes_na_tranche = []
    for _ in range(tranche_sem_cliff):
        acoes_na_tranche = math.floor(total_acoes / tranche_sem_cliff)
        lista_acoes_na_tranche.append(acoes_na_tranche)
    soma_acoes_no_cliff = sum(lista_acoes_na_tranche[:tranches_no_cliff])
    lista_acoes_na_tranche[-1] += acoes_restantes
    nova_lista = [soma_acoes_no_cliff] + lista_acoes_na_tranche[tranches_no_cliff:]
    return nova_lista


def fractional(total_acoes, tranche_sem_cliff, tranches_no_cliff):
    lista_acoes_na_tranche = []
    for _ in range(tranche_sem_cliff):
        acoes_na_tranche = round(total_acoes / tranche_sem_cliff, 4)
        lista_acoes_na_tranche.append(acoes_na_tranche)
    soma_acoes_no_cliff = sum(lista_acoes_na_tranche[:tranches_no_cliff])
    sobra = total_acoes - sum(lista_acoes_na_tranche)
    nova_lista = [soma_acoes_no_cliff + sobra] + [round(x, 4) for x in lista_acoes_na_tranche[tranches_no_cliff:]]
    nova_lista = [round(x, 4) for x in nova_lista]
    return nova_lista


@app.post("/calendario_vesting", summary="Calcula o calendário de vesting com base nos parâmetros fornecidos.")
def calcular_vesting(params: VestingParams):
    # Calcular Tranches
    tranche_sem_cliff = math.ceil(params.vesting / params.periodicidade)
    tranches_no_cliff = math.ceil(params.cliff / params.periodicidade)
    total_tranches = math.ceil(tranche_sem_cliff - tranches_no_cliff + 1)

    # Calcular a quantidade de ações por vesting
    acoes_por_vesting = params.total_acoes / params.vesting

    # Calcular a quantidade de ações no período
    acoes_periodo = acoes_por_vesting * params.periodicidade

    # Calcular a quantidade de ações restantes
    acoes_restantes = params.total_acoes - math.floor(acoes_periodo) * tranche_sem_cliff

    # Gerar datas de vesting
    datas_vesting = gerar_datas_vesting(params.data_inicio_vesting, total_tranches, params.periodicidade)

    # Selecionar a forma de arredondamento
    if params.arredondamento == 1:
        quantidade_acoes = cumulative_rounding(params.total_acoes, tranche_sem_cliff, tranches_no_cliff)
    elif params.arredondamento == 2:
        quantidade_acoes = cumulative_rounding_down(params.total_acoes, tranche_sem_cliff, tranches_no_cliff)
    elif params.arredondamento == 3:
        quantidade_acoes = front_loaded(params.total_acoes, tranche_sem_cliff, tranches_no_cliff)
    elif params.arredondamento == 4:
        quantidade_acoes = back_loaded(params.total_acoes, tranche_sem_cliff, tranches_no_cliff, params.cliff)
    elif params.arredondamento == 5:
        quantidade_acoes = front_loaded_to_single_tranche(params.total_acoes, tranche_sem_cliff, tranches_no_cliff, acoes_restantes)
    elif params.arredondamento == 6:
        quantidade_acoes = back_loaded_to_single_tranche(params.total_acoes, tranche_sem_cliff, tranches_no_cliff, acoes_restantes)
    elif params.arredondamento == 7:
        quantidade_acoes = fractional(params.total_acoes, tranche_sem_cliff, tranches_no_cliff)
    else:
        raise HTTPException(status_code=400, detail="Escolha um valor válido")

    # Criar o dicionário combinando datas e quantidades de ações
    vesting_dict = {datas_vesting[i]: quantidade_acoes[i] for i in range(len(datas_vesting))}

    # Retornar o JSON resultante
    return vesting_dict
