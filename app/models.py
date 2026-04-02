from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, Boolean, Text, Date, String
from sqlalchemy.orm import relationship
from datetime import datetime

db = SQLAlchemy()

class Departamento(db.Model):
    __tablename__ = 'departamento'
    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)

class Obra(db.Model):
    __tablename__ = 'obra'
    id = Column(Integer, primary_key=True)
    nome = Column(String(150), nullable=False)

class Familia(db.Model):
    __tablename__ = 'familia'
    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    tipos = relationship('Tipo', backref='familia', lazy=True)
    skus = relationship('Sku', back_populates='familia')

class Tipo(db.Model):
    __tablename__ = 'tipo'
    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    
    # Chave estrangeira: armazena o ID da Família
    familia_id = Column(Integer, ForeignKey('familia.id'), nullable=False)
    skus = relationship('Sku', back_populates='tipo')

class Especificacao(db.Model):
    __tablename__ = 'especificacao'
    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)

class User(db.Model):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(150), unique=True, nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password = Column(String(150), nullable=True)
    classe = Column(String(50), default='user')
    first_login_completed = Column(Boolean, default=False)
    active = Column(Boolean, default=True)
    
    ramal = Column(String(20))
    numero_corporativo = Column(String(20))
    cargo = Column(String(50))
    
    departamento_id = Column(Integer, ForeignKey('departamento.id'))
    obra_id = Column(Integer, ForeignKey('obra.id'))
    
    # Relacionamento para saber quais equipamentos da empresa estão com ele
    patrimonios = relationship("Patrimonio", back_populates="usuario_responsavel")

class Sku(db.Model):
    __tablename__ = 'sku'
    id = Column(Integer, primary_key=True)
    
    codigo = Column(String(100), nullable=False, unique=True)
    nome = Column(String(200), nullable=False)
    
    familia_id = Column(Integer, ForeignKey('familia.id'), nullable=True)
    tipo_id = Column(Integer, ForeignKey('tipo.id'), nullable=True)
    familia = relationship("Familia", back_populates="skus")
    tipo = relationship("Tipo", back_populates="skus")

    especificacao_id = Column(Integer, ForeignKey('especificacao.id'), nullable=True)
    especificacao = relationship("Especificacao")
    
    marca_id = Column(Integer, ForeignKey('marca.id'), nullable=True)
    marca = relationship("Marca", back_populates="skus")
    
    peso = Column(Float, nullable=True)      
    valorPeso = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    produtos_em_estoque = relationship("Produto", back_populates="sku")
    ativos_patrimonio = relationship("Patrimonio", back_populates="sku")

class Marca(db.Model):
    __tablename__ = 'marca'
    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False, unique=True)
    
    skus = relationship("Sku", back_populates="marca")

class Produto(db.Model):
    __tablename__ = 'produto'
    id = Column(Integer, primary_key=True)

    sku_id = Column(Integer, ForeignKey('sku.id'), nullable=False)
    sku = relationship("Sku", back_populates="produtos_em_estoque")

    quantidade = Column(Float, default=0.0) 
    
    corredor = Column(String(50), nullable=True)   
    prateleira = Column(String(50), nullable=True) 
    
    preco = Column(Float, nullable=False) 
    preco_promocional = Column(Float, nullable=True) 
    data_validade = Column(Date, nullable=True) 

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ativo = Column(Boolean, default=True)

    def obter_preco_venda_atual(self):
        if self.preco_promocional and self.preco_promocional > 0:
            return self.preco_promocional
        return self.preco

    def calcular_preco_por_peso(self, peso_lido_na_balanca):
        if not self.sku.valorPeso or not self.sku.peso or self.sku.peso <= 0:
            return 0.0
        multiplicador = peso_lido_na_balanca / self.sku.peso
        return round(multiplicador * self.sku.valorPeso, 2)

class Patrimonio(db.Model):
    __tablename__ = 'patrimonio'
    id = Column(Integer, primary_key=True)
    
    # Identificação Única
    codigo_patrimonio = Column(String(50), unique=True, nullable=False) # Ex: TI-00124 (Plaqueta)
    numero_serie = Column(String(100), unique=True, nullable=True)      # S/N do Fabricante
    
    # Vinculando ao Catálogo (Sabemos que é um "Dell Inspiron 15" através do SKU)
    sku_id = Column(Integer, ForeignKey('sku.id'), nullable=False)
    sku = relationship("Sku", back_populates="ativos_patrimonio")
    
    # Localização / Responsabilidade
    user_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    usuario_responsavel = relationship("User", back_populates="patrimonios")
    
    # Ex: Disponível, Em Uso, Em Manutenção, Furtado, Descartado
    status = Column(String(50), default='Disponível') 
    
    # Dados de Compra/Garantia específicos deste item
    data_compra = Column(Date, nullable=True)
    fim_garantia = Column(Date, nullable=True)
    valor_compra = Column(Float, nullable=True)
    
    observacoes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)