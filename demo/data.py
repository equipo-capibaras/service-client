from datetime import UTC, datetime

from models import Client, Employee, InvitationStatus, Plan, Role

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
        invitation_status=InvitationStatus.ACCEPTED,
        invitation_date=datetime(2024, 10, 10, 17, 56, 55, tzinfo=UTC),
    ),
    Employee(
        id='906ee75c-2bfd-4478-8f8e-da8b7fede94d',
        client_id=client_universo.id,
        name='Maria Silva Oliveira',
        email='maria.silva@universo.br',
        password='$pbkdf2-sha256$29000$9f6fU0rpPYcQopRybq1VSg$MPkE3PyeoRa.iDh5FPS/5DAqFUqpS/B8iWnjmnFOa6A',  # noqa: S106
        role=Role.ANALYST,
        invitation_status=InvitationStatus.ACCEPTED,
        invitation_date=datetime(2024, 10, 12, 14, 26, 22, tzinfo=UTC),
    ),
    Employee(
        id='7ecbab00-726e-4c21-b7ea-17fa2ace7b1d',
        client_id=client_universo.id,
        name='João Pedro Santos',
        email='joao.santos@universo.br',
        password='$pbkdf2-sha256$29000$co6Rsrb2vncupfT.39v7/w$fnenIA46DpG7.BJ.CqmqQ7MB1try3Pu91b1dQrKZZlo',  # noqa: S106
        role=Role.AGENT,
        invitation_status=InvitationStatus.ACCEPTED,
        invitation_date=datetime(2024, 10, 13, 15, 11, 12, tzinfo=UTC),
    ),
    Employee(
        id='544d24df-1e09-4115-b465-13025e7bbfc5',
        client_id=client_universo.id,
        name='Ana Clara Oliveira',
        email='ana.oliveira@universo.br',
        password='$pbkdf2-sha256$29000$jTGm1DoHQKg15lyLUSolBA$V2eRaq5OQN0P.0PGM38PjMhIgGBh5Ig9a8rIS.XoYcM',  # noqa: S106
        role=Role.AGENT,
        invitation_status=InvitationStatus.ACCEPTED,
        invitation_date=datetime(2024, 10, 15, 8, 15, 42, tzinfo=UTC),
    ),
    Employee(
        id='ec953b05-f153-4193-b357-9f2327d54281',
        client_id=client_universo.id,
        name='José Augusto Ferreira',
        email='jose.ferreira@universo.br',
        password='$pbkdf2-sha256$29000$4Pwfw1iLkRLivNd6L2WstQ$TdXjoSU1Tc0cUcO00QHMnTWb7/KPLoscrtLyHxo0cPw',  # noqa: S106
        role=Role.ANALYST,
        invitation_status=InvitationStatus.PENDING,
        invitation_date=datetime(2024, 10, 16, 14, 32, 18, tzinfo=UTC),
    ),
    Employee(
        id='64843bfd-2501-4e57-84de-1826ae3e5d88',
        client_id=client_universo.id,
        name='Marcos Vinicius Rodrigues',
        email='marcos.rodrigues@universo.br',
        password='$pbkdf2-sha256$29000$eS.FsLZ2rvVeKyVE6L2Xkg$sZMG7Wymswf7J2EPCu7kR0q9E0kr83aSnextc1ajiSw',  # noqa: S106
        role=Role.AGENT,
        invitation_status=InvitationStatus.ACCEPTED,
        invitation_date=datetime(2024, 10, 17, 9, 48, 53, tzinfo=UTC),
    ),
    Employee(
        id='7293a54c-3e1b-4f96-a66e-d44cdc4e5f6b',
        client_id=client_universo.id,
        name='Juliana Cristina Pereira',
        email='juliana.pereira@universo.br',
        password='$pbkdf2-sha256$29000$KAUgJITwHkNo7b13TiklBA$9G0LqSSHqXigFdCrhbBHdSecBRtUAZlwCfN/.0iaRYg',  # noqa: S106
        role=Role.AGENT,
        invitation_status=InvitationStatus.PENDING,
        invitation_date=datetime(2024, 10, 18, 11, 21, 6, tzinfo=UTC),
    ),
    Employee(
        id='c18608fb-5f19-4389-a232-1104375fa468',
        client_id=client_universo.id,
        name='Lucas Gabriel Ferreira',
        email='lucas.ferreira@universo.br',
        password='$pbkdf2-sha256$29000$730PwVgLQehdy3lPSamVEg$AHNuK/3qxcADCI655V/Eiw3pjVZmlLDySP4B7p4cS0A',  # noqa: S106
        role=Role.AGENT,
        invitation_status=InvitationStatus.PENDING,
        invitation_date=datetime(2024, 10, 17, 11, 52, 35, tzinfo=UTC),
    ),
    Employee(
        id='d2ca7892-35f6-4680-b71c-1559c133997e',
        client_id=client_universo.id,
        name='Pedro Henrique Oliveira',
        email='pedro.oliveira@universo.br',
        password='$pbkdf2-sha256$29000$CEFISWlNKcU453wPQSjF.A$SzZltRRrxBClKB1FwzNjhYKI90refcsXH8.HfTHLfm8',  # noqa: S106
        role=Role.AGENT,
        invitation_status=InvitationStatus.PENDING,
        invitation_date=datetime(2024, 10, 15, 16, 38, 17, tzinfo=UTC),
    ),
    Employee(
        id='0a3b230a-3a9b-48a9-8868-5c58f7e8384c',
        client_id=client_universo.id,
        name='Laura Sophia Castro',
        email='laura.castro@universo.br',
        password='$pbkdf2-sha256$29000$2RsjRMj5vzcmBKCUMgaA8A$9Da9tMhwS87E5ip2uRkbzhAOB8926UVBJmzm4Eo.PK8',  # noqa: S106
        role=Role.AGENT,
        invitation_status=InvitationStatus.ACCEPTED,
        invitation_date=datetime(2024, 10, 18, 16, 35, 7, tzinfo=UTC),
    ),
    Employee(
        id='5c1b18fe-8583-48d2-b4cc-b279e5d514d7',
        client_id=client_universo.id,
        name='Bianca Rebeca Cardoso',
        email='bianca.cardoso@universo.br',
        password='$pbkdf2-sha256$29000$5Nz7XytFCMF477231jpnrA$t/TUtqprrZzoVvp.TllmU9ky.Te2yrTHlrMXzmRVJy0',  # noqa: S106
        role=Role.AGENT,
        invitation_status=InvitationStatus.PENDING,
        invitation_date=datetime(2024, 10, 16, 9, 42, 28, tzinfo=UTC),
    ),
    Employee(
        id='d2bb55d7-3306-4f12-9d23-10437f7244f0',
        client_id=client_universo.id,
        name='Helena Cecília Moraes',
        email='helena.moraes@universo.br',
        password='$pbkdf2-sha256$29000$C.H8f6.VshbCOGfMWSvF.A$k6mT1f4ioUm0/WU3ja50m2dCdSwEuA4DU2l700svDbA',  # noqa: S106
        role=Role.ANALYST,
        invitation_status=InvitationStatus.ACCEPTED,
        invitation_date=datetime(2024, 10, 19, 16, 12, 24, tzinfo=UTC),
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
        invitation_date=datetime(2024, 10, 11, 15, 11, 12, tzinfo=UTC),
    ),
    Employee(
        id='1dabcf78-e62a-41fd-b69c-fd7c775b04d4',
        client_id=client_globalcom.id,
        name='Mariana Sanchez Torres',
        email='mariana@globalcom.ec',
        password='$pbkdf2-sha256$29000$I6S0dm4tRSjFuBdCqJXy3g$FRrF180nHvi3UV4HVvV48hzuSTdbLDjx/oTvqFZty.8',  # noqa: S106
        role=Role.ANALYST,
        invitation_status=InvitationStatus.ACCEPTED,
        invitation_date=datetime(2024, 10, 12, 16, 32, 48, tzinfo=UTC),
    ),
    Employee(
        id='b15960ec-e058-4ed7-8721-39925c810583',
        client_id=client_globalcom.id,
        name='Luciana Vargas Arango',
        email='luciana@globalcom.ec',
        password='$pbkdf2-sha256$29000$O6fU.l8LgbDWGsN4T0kJwQ$rJh0O1YIK22vpo34fiSbJcSNIWOzhTWjzywEYpMgGAo',  # noqa: S106
        role=Role.AGENT,
        invitation_status=InvitationStatus.ACCEPTED,
        invitation_date=datetime(2024, 10, 12, 11, 45, 37, tzinfo=UTC),
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
        invitation_status=InvitationStatus.ACCEPTED,
        invitation_date=datetime(2024, 10, 15, 11, 45, 15, tzinfo=UTC),
    ),
    Employee(
        id='e7ae844f-ae95-4d04-8d45-0a155ce58bcc',
        client_id=client_gigatel.id,
        name='Miguel Diaz Flores',
        email='miguel.diaz.flores@gigatel.co',
        password='$pbkdf2-sha256$29000$a02J0boXYqyVsnaOcW6t1Q$fsd6x5xNR1vZHOKT1utssQ6RTmo0EPlm9OsEXC55mCo',  # noqa: S106
        role=Role.ANALYST,
        invitation_status=InvitationStatus.ACCEPTED,
        invitation_date=datetime(2024, 10, 16, 11, 27, 39, tzinfo=UTC),
    ),
    Employee(
        id='0abad006-921c-4e09-b2a6-10713b71571f',
        client_id=client_gigatel.id,
        name='Julian Cordoba Rincón',
        email='julian.cordoba.rincon@gigatel.co',
        password='$pbkdf2-sha256$29000$/L93bo3R.h.DUOq917p3Dg$OJ6VIcC5j7s8ITKP6Kk4n2k2leXGU/5OA3gj6sX8y/Y',  # noqa: S106
        role=Role.AGENT,
        invitation_status=InvitationStatus.ACCEPTED,
        invitation_date=datetime(2024, 10, 16, 22, 45, 37, tzinfo=UTC),
    ),
]

# Unassigned
employees_unassigned = [
    Employee(
        id='48b93bd9-492d-4b05-b38d-6ee4d2d83728',
        client_id=None,
        name='Sofia Martinez Lopez',
        email='sofia@gigatel.co',
        password='$pbkdf2-sha256$29000$LQWA0FqLsTbm3JtTas1Zyw$aakebPeV.Ex.El4ZTaAMeopJ8ArQPZgB1uKb8hunVig',  # noqa: S106
        role=Role.ANALYST,
        invitation_status=InvitationStatus.UNINVITED,
        invitation_date=datetime(2024, 10, 9, 8, 25, 51, tzinfo=UTC),
    ),
    Employee(
        id='e658bffa-d2a0-4ed4-9863-bbcd8939d978',
        client_id=None,
        name='Lucia Gonzalez Fernandez',
        email='lucia@globalcom.ec',
        password='$pbkdf2-sha256$29000$U.q917r3ntNaK2VMibE2Bg$gZOEg.vzYmKUf0n3hNxUSUBCdpUwxv6OHGqnTuzWyHw',  # noqa: S106
        role=Role.AGENT,
        invitation_status=InvitationStatus.UNINVITED,
        invitation_date=datetime(2024, 10, 10, 5, 47, 23, tzinfo=UTC),
    ),
]

clients = [client_universo, client_globalcom, client_gigatel]
employees = employees_universo + employees_globalcom + employees_gigatel + employees_unassigned
