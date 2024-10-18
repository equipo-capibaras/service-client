from datetime import UTC, datetime

from models import Client, Employee, Plan, Role
from models.employee import InvitationStatus

# Universo Móvel
client_universo = Client(
    id='acfa53b4-58f3-46e8-809b-19ef52b437ed',
    name='Universo Móvel',
    plan=Plan.EMPRENDEDOR,
    email_incidents='universo@capibaras.io',
)

employees_universo = [
    Employee(
        id='099416a5-e094-4274-9901-cc07f686e50a',
        client_id=client_universo.id,
        name='Bernardo Lima Abreu',
        email='bernardo.abreu@universo.br',
        password='$pbkdf2-sha256$29000$qpWylrI2BqD03rtXam3tvQ$avheO0yxd1O56eB0KSx6ynDjkljJrc46tcHf24iWsoc',  # noqa: S106
        role=Role.ADMIN,
    ),
    Employee(
        id='906ee75c-2bfd-4478-8f8e-da8b7fede94d',
        client_id=client_universo.id,
        name='Maria Silva Oliveira',
        email='maria.silva@universo.br',
        password='$pbkdf2-sha256$29000$9f6fU0rpPYcQopRybq1VSg$MPkE3PyeoRa.iDh5FPS/5DAqFUqpS/B8iWnjmnFOa6A',  # noqa: S106
        role=Role.ANALYST,
    ),
    Employee(
        id='7ecbab00-726e-4c21-b7ea-17fa2ace7b1d',
        client_id=client_universo.id,
        name='João Pedro Santos',
        email='joao.santos@universo.br',
        password='$pbkdf2-sha256$29000$co6Rsrb2vncupfT.39v7/w$fnenIA46DpG7.BJ.CqmqQ7MB1try3Pu91b1dQrKZZlo',  # noqa: S106
        role=Role.AGENT,
    ),
]

# GlobalCom
client_globalcom = Client(
    id='22128c04-0c2c-4633-8317-0fffd552f7a6',
    name='GlobalCom',
    plan=Plan.EMPRESARIO,
    email_incidents='globalcom@capibaras.io',
)

employees_globalcom = [
    Employee(
        id='db9dd866-346f-46a7-b4fe-6d5573597e3d',
        client_id=client_globalcom.id,
        name='Emiliano Giraldo Velasquez',
        email='emiliano@globalcom.ec',
        password='$pbkdf2-sha256$29000$k5JSyvn/nzPmPGfM2Tun1A$fnAMQpvDOQ8r6ZpQfh0IWd5Dz6eTj7NmgpDgeuJBxeM',  # noqa: S106
        role=Role.ADMIN,
        invitation_status=InvitationStatus.ACCEPTED,
        invitation_date=datetime.now(UTC),
    ),
    Employee(
        id='1dabcf78-e62a-41fd-b69c-fd7c775b04d4',
        client_id=client_globalcom.id,
        name='Mariana Sanchez Torres',
        email='mariana@globalcom.ec',
        password='$pbkdf2-sha256$29000$I6S0dm4tRSjFuBdCqJXy3g$FRrF180nHvi3UV4HVvV48hzuSTdbLDjx/oTvqFZty.8',  # noqa: S106
        role=Role.ANALYST,
        invitation_status=InvitationStatus.ACCEPTED,
        invitation_date=datetime.now(UTC),
    ),
    Employee(
        id='b15960ec-e058-4ed7-8721-39925c810583',
        client_id=client_globalcom.id,
        name='Luciana Vargas Arango',
        email='luciana@globalcom.ec',
        password='$pbkdf2-sha256$29000$O6fU.l8LgbDWGsN4T0kJwQ$rJh0O1YIK22vpo34fiSbJcSNIWOzhTWjzywEYpMgGAo',  # noqa: S106
        role=Role.AGENT,
        invitation_status=InvitationStatus.PENDING,
        invitation_date=datetime.now(UTC),
    ),
]

# Gigatel
client_gigatel = Client(
    id='9a652818-342e-4771-84cf-39c20a29264d',
    name='GigaTel',
    plan=Plan.EMPRESARIO_PLUS,
    email_incidents='gigatel@capibaras.io',
)

employees_gigatel = [
    Employee(
        id='87caee53-ab01-4dea-80bf-5c044364f94b',
        client_id=client_gigatel.id,
        name='Cielo Guerrero Rivera',
        email='cielo.guerrero.rivera@gigatel.co',
        password='$pbkdf2-sha256$29000$5vwfw9g7x1jrXQthLMUYww$nonWNNpQ.656o2KHv.zPZcl7ILX.gsKtGPLkazWj9u4',  # noqa: S106
        role=Role.ADMIN,
    ),
    Employee(
        id='e7ae844f-ae95-4d04-8d45-0a155ce58bcc',
        client_id=client_gigatel.id,
        name='Miguel Diaz Flores',
        email='miguel.diaz.flores@gigatel.co',
        password='$pbkdf2-sha256$29000$a02J0boXYqyVsnaOcW6t1Q$fsd6x5xNR1vZHOKT1utssQ6RTmo0EPlm9OsEXC55mCo',  # noqa: S106
        role=Role.ANALYST,
    ),
    Employee(
        id='0abad006-921c-4e09-b2a6-10713b71571f',
        client_id=client_gigatel.id,
        name='Julian Cordoba Rincón',
        email='julian.cordoba.rincon@gigatel.co',
        password='$pbkdf2-sha256$29000$/L93bo3R.h.DUOq917p3Dg$OJ6VIcC5j7s8ITKP6Kk4n2k2leXGU/5OA3gj6sX8y/Y',  # noqa: S106
        role=Role.AGENT,
    ),
]

# Unassigned
employees_unassigned = [
    Employee(
        id='e7ae844f-ae95-4d04-8d45-0a155ce58bcc',
        client_id=None,
        name='Sofia Martinez Lopez',
        email='sofia@gigatel.co',
        password='$pbkdf2-sha256$29000$LQWA0FqLsTbm3JtTas1Zyw$aakebPeV.Ex.El4ZTaAMeopJ8ArQPZgB1uKb8hunVig',  # noqa: S106
        role=Role.ANALYST,
    ),
    Employee(
        id='0abad006-921c-4e09-b2a6-10713b71571f',
        client_id=None,
        name='Lucia Gonzalez Fernandez',
        email='lucia@globalcom.ec',
        password='$pbkdf2-sha256$29000$U.q917r3ntNaK2VMibE2Bg$gZOEg.vzYmKUf0n3hNxUSUBCdpUwxv6OHGqnTuzWyHw',  # noqa: S106
        role=Role.AGENT,
    ),
]

clients = [client_universo, client_globalcom, client_gigatel]
employees = employees_universo + employees_globalcom + employees_gigatel + employees_unassigned
