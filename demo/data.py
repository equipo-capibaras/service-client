from typing import TypedDict, NotRequired

Employee = TypedDict('Employee', {
    'id': NotRequired[str],
    'name': str,
    'email': str,
    'password': str,
    'role': str
})

Client = TypedDict('Client', {
    'id': NotRequired[str],
    'name': str,
    'plan': str,
    'emailIncidents': str,
    'employees': NotRequired[list[Employee]]
})

clients: list[Client] = [
    {
        'id': 'acfa53b4-58f3-46e8-809b-19ef52b437ed',
        'name': 'Universo Móvel',
        'plan': 'EMPRENDEDOR',
        'emailIncidents': 'universo@capibaras.io',
        'employees': [
            {
                'id': '099416a5-e094-4274-9901-cc07f686e50a',
                'name': 'Bernardo Lima Abreu',
                'email': 'bernardo.abreu@universo.br',
                'password': '$pbkdf2-sha256$29000$qpWylrI2BqD03rtXam3tvQ$avheO0yxd1O56eB0KSx6ynDjkljJrc46tcHf24iWsoc',
                'role': 'ADMIN'
            },
            {
                'id': '906ee75c-2bfd-4478-8f8e-da8b7fede94d',
                'name': 'Maria Silva Oliveira',
                'email': 'maria.silva@universo.br',
                'password': '$pbkdf2-sha256$29000$9f6fU0rpPYcQopRybq1VSg$MPkE3PyeoRa.iDh5FPS/5DAqFUqpS/B8iWnjmnFOa6A',
                'role': 'ANALYST'
            },
            {
                'id': '7ecbab00-726e-4c21-b7ea-17fa2ace7b1d',
                'name': 'João Pedro Santos',
                'email': 'joao.santos@universo.br',
                'password': '$pbkdf2-sha256$29000$co6Rsrb2vncupfT.39v7/w$fnenIA46DpG7.BJ.CqmqQ7MB1try3Pu91b1dQrKZZlo',
                'role': 'AGENT'
            },
        ]
    },
    {
        'id': '22128c04-0c2c-4633-8317-0fffd552f7a6',
        'name': 'GlobalCom',
        'plan': 'EMPRESARIO',
        'emailIncidents': 'globalcom@capibaras.io',
        'employees': [
            {
                'id': 'db9dd866-346f-46a7-b4fe-6d5573597e3d',
                'name': 'Emiliano Giraldo Velasquez',
                'email': 'emiliano@globalcom.ec',
                'password': '$pbkdf2-sha256$29000$k5JSyvn/nzPmPGfM2Tun1A$fnAMQpvDOQ8r6ZpQfh0IWd5Dz6eTj7NmgpDgeuJBxeM',
                'role': 'ADMIN'
            },
            {
                'id': '1dabcf78-e62a-41fd-b69c-fd7c775b04d4',
                'name': 'Mariana Sanchez Torres',
                'email': 'mariana@globalcom.ec',
                'password': '$pbkdf2-sha256$29000$I6S0dm4tRSjFuBdCqJXy3g$FRrF180nHvi3UV4HVvV48hzuSTdbLDjx/oTvqFZty.8',
                'role': 'ANALYST'
            },
            {
                'id': 'b15960ec-e058-4ed7-8721-39925c810583',
                'name': 'Luciana Vargas Arango',
                'email': 'luciana@globalcom.ec',
                'password': '$pbkdf2-sha256$29000$O6fU.l8LgbDWGsN4T0kJwQ$rJh0O1YIK22vpo34fiSbJcSNIWOzhTWjzywEYpMgGAo',
                'role': 'AGENT'
            },
        ]
    },
    {
        'id': '9a652818-342e-4771-84cf-39c20a29264d',
        'name': 'GigaTel',
        'plan': 'EMPRESARIO_PLUS',
        'emailIncidents': 'gigatel@capibaras.io',
        'employees': [
            {
                'id': '87caee53-ab01-4dea-80bf-5c044364f94b',
                'name': 'Cielo Guerrero Rivera',
                'email': 'cielo.guerrero.rivera@gigatel.co',
                'password': '$pbkdf2-sha256$29000$5vwfw9g7x1jrXQthLMUYww$nonWNNpQ.656o2KHv.zPZcl7ILX.gsKtGPLkazWj9u4',
                'role': 'ADMIN'
            },
            {
                'id': 'e7ae844f-ae95-4d04-8d45-0a155ce58bcc',
                'name': 'Miguel Diaz Flores',
                'email': 'miguel.diaz.flores@gigatel.co',
                'password': '$pbkdf2-sha256$29000$a02J0boXYqyVsnaOcW6t1Q$fsd6x5xNR1vZHOKT1utssQ6RTmo0EPlm9OsEXC55mCo',
                'role': 'ANALYST'
            },
            {
                'id': '0abad006-921c-4e09-b2a6-10713b71571f',
                'name': 'Julian Cordoba Rincón',
                'email': 'julian.cordoba.rincon@gigatel.co',
                'password': '$pbkdf2-sha256$29000$/L93bo3R.h.DUOq917p3Dg$OJ6VIcC5j7s8ITKP6Kk4n2k2leXGU/5OA3gj6sX8y/Y',
                'role': 'AGENT'
            },
        ]
    }
]
